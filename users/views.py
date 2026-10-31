from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action 
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializers import RegisterSerializer, ProfileSerializer
from posts.serializers import CommentSerializer
from posts.models import Comment

from posts.serializers import PostSerializer
from posts.models import Post

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User registered successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TestAuthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "message": f"Hello {request.user.username}, you are authenticated"
        })
    
class ProfileView(APIView):
    def get(self, request, username):
        user = User.objects.get(username=username)

        profile_data = ProfileSerializer(user).data

        posts = Post.objects.filter(user=user).order_by("-created_at")

        replies = Comment.objects.filter(user=user).order_by("-created_at")

        likes = Post.objects.filter(likes__user=user).order_by("-created_at")

        return Response({
            "profile": profile_data,
            "posts": PostSerializer(posts, many=True).data,
            "replies": CommentSerializer(replies, many=True).data,
            "likes": PostSerializer(likes, many=True).data 
        })
    

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = ProfileSerializer

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def follow(self, request, pk=None):

        user_to_follow = self.get_object()
        user = request.user

        if user in user_to_follow.followers.all():
            user_to_follow.followers.remove(user)

            return Response({"status": "unfollowed"})
        else:
            user_to_follow.followers.add(user)
            return Response({"status": "followed"})