from rest_framework import serializers
from .models import Post, Comment, Follow, PostMedia

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='user.username', read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'author', 'post', 'parent', 'replies', 'content', 'created_at']
    
    def get_replies(self, obj):
        replies = obj.replies.all()
        return CommentSerializer(replies, many=True).data


class PostMediaSerializer(serializers.ModelSerializer):

    class Meta:
        model = PostMedia
        fields = ["id", "type", "file"]
    
    def get_file(self, obj):
        request = self.context.get("request")
        if request is not None:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url


class ParentPostSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="user.username", read_only=True)
    media = PostMediaSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ["id", "author", "content", "media", "created_at"]


class PostSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='user.username', read_only=True)
    media = PostMediaSerializer(many=True, read_only=True)

    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    repost_count = serializers.IntegerField(read_only=True)

    is_liked = serializers.BooleanField(read_only=True)
    is_reposted = serializers.BooleanField(read_only=True)
    is_repost = serializers.SerializerMethodField()

    parent = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'content', 'media',
            'like_count', 'comment_count', 'repost_count',
            'is_liked', 'is_reposted', 'is_repost',
            'parent', 'created_at', 'updated_at'
        ]

    def get_is_repost(self, obj):
        return obj.parent is not None

    def get_parent(self, obj):
        if obj.parent:
            return ParentPostSerializer(obj.parent, context=self.context).data
        return None

    def validate(self, attrs):
        request = self.context.get("request")
        content = (attrs.get("content") or "").strip()
        has_media = bool(request and request.FILES.getlist("media"))

        if self.instance is None and not content and not has_media:
            raise serializers.ValidationError(
                "A post needs some text or at least one file."
            )
        return attrs


class FollowSerializer(serializers.ModelSerializer):

    class Meta: 
        model = Follow
        fields = "__all__"
        read_only_fields = ["follower"]

    