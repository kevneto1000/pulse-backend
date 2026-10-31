from rest_framework import viewsets
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView 
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework import status
from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Exists, OuterRef, Case, When, F, Value, IntegerField, Subquery
from django.db.models.functions import Coalesce
from .permissions import IsOwnerOrReadOnly, IsCommentOwner
from .models import Post, Like, Comment, Follow, PostMedia
from users.models import User
from .serializers import PostSerializer, CommentSerializer, FollowSerializer
from users.serializers import ProfileSerializer

class PostViewSet(ModelViewSet):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        post = serializer.save(user=self.request.user)

        media_files = self.request.FILES.getlist("media")

        for media in media_files:
            if str(media.content_type).startswith("image"):
                media_type = "image"
            elif str(media.content_type).startswith("video"):
                media_type = "video"
            else:
                media_type = "file"
            
            PostMedia.objects.create(post=post, file=media, type=media_type)


    def get_queryset(self):
        user = self.request.user

        def count_for(model, field):
            return Coalesce(
                Subquery(
                    model.objects.filter(**{field: OuterRef("root_id")})
                    .order_by()
                    .values(field)
                    .annotate(c=Count("id"))
                    .values("c")
                ),
                0,
            )

        queryset = (
            Post.objects.select_related("user", "parent__user")
            .prefetch_related("media", "parent__media")
            .annotate(
                root_id=Case(
                    When(parent__isnull=True, then=F("id")),
                    default=F("parent_id"),
                    output_field=IntegerField(),
                )
            )
            .annotate(
                like_count=count_for(Like, "post"),
                comment_count=count_for(Comment, "post"),
                repost_count=count_for(Post, "parent"),
            )
        )

        if user.is_authenticated:
            queryset = queryset.annotate(
                is_liked=Exists(Like.objects.filter(post=OuterRef("root_id"), user=user)),
                is_reposted=Exists(Post.objects.filter(parent=OuterRef("root_id"), user=user)),
            )

        return queryset.order_by("-created_at")
    


    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        target = post.parent or post

        like, created = Like.objects.get_or_create(user=request.user, post=target)

        if not created: 
            like.delete()
            return Response({'message': "Post unliked"})
        
        return Response({"message": "Post liked"})
        
    
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def feed(self, request):
        user = request.user

        following_users = user.following.values_list("following", flat=True)

        posts = self.get_queryset().filter(
            Q(user__in=following_users) | Q(user=user)
        )

        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
    
    
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def repost(self, request, pk=None):
        original_post = self.get_object()
        user = request.user
        content = request.data.get("content", "")

        
        if original_post.parent:
            original_post = original_post.parent

        existing_repost = Post.objects.filter(
            user=user,
            parent=original_post
        ).first()

        
        if existing_repost:
            existing_repost.delete()
            return Response({"message": "Repost removed"})

        try:
            with transaction.atomic():
                repost = Post.objects.create(
                    user=user,
                    parent=original_post,
                    content=content
                )
        except IntegrityError:
            return Response({"message": "Already reposted"}, status=status.HTTP_409_CONFLICT)

        serializer = self.get_serializer(repost)
        return Response(serializer.data, status=201)
    

class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        post_id = self.request.query_params.get("post")

        queryset = Comment.objects.filter(parent__isnull=True).order_by("created_at")

        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset



    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsCommentOwner()]
        return super().get_permissions()
    


class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Follow.objects.filter(follower=self.request.user)
    
    def perform_create(self, serializer):
        if self.request.user == serializer.validated_data["following"]:
            raise ValidationError("You cannot follow yourself.")
        serializer.save(follower=self.request.user)


    @action(detail=False, methods=["post"])
    def toggle(self, request):
        user_to_follow_id = request.data.get("user_id")

        if not user_to_follow_id:
            return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_to_follow = User.objects.get(id=user_to_follow_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if user_to_follow == request.user:
            return Response({"error": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)

        follow, created = Follow.objects.get_or_create(follower=request.user, following=user_to_follow)

        if not created:
            follow.delete()
            return Response({"message": "Unfollowed"}, status=status.HTTP_200_OK)
        return Response({"message": "Followed"}, status=status.HTTP_201_CREATED)

    
    