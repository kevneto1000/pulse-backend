from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User
from .models import Post, Like, Follow


class PostTests(APITestCase):
    def setUp(self):
        # Runs before every test: creates two users
        self.alice = User.objects.create_user("alice", "alice@example.com", "pass12345")
        self.bob = User.objects.create_user("bob", "bob@example.com", "pass12345")

    def test_create_post_requires_login(self):
        response = self.client.post("/api/posts/", {"content": "hi"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post(self):
        self.client.force_authenticate(self.alice)
        response = self.client.post("/api/posts/", {"content": "hello"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.first().user, self.alice)

    def test_empty_post_rejected(self):
        self.client.force_authenticate(self.alice)
        response = self.client.post("/api/posts/", {"content": "   "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Post.objects.count(), 0)

    def test_cannot_delete_someone_elses_post(self):
        post = Post.objects.create(user=self.alice, content="mine")
        self.client.force_authenticate(self.bob)
        response = self.client.delete(f"/api/posts/{post.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Post.objects.filter(id=post.id).exists())

    def test_like_toggles_on_and_off(self):
        post = Post.objects.create(user=self.alice, content="x")
        self.client.force_authenticate(self.bob)
        url = f"/api/posts/{post.id}/like/"

        self.client.post(url)
        self.assertEqual(Like.objects.filter(post=post).count(), 1)

        self.client.post(url)
        self.assertEqual(Like.objects.filter(post=post).count(), 0)

    def test_liking_a_repost_likes_the_original(self):
        original = Post.objects.create(user=self.alice, content="x")
        repost = Post.objects.create(user=self.bob, parent=original)
        self.client.force_authenticate(self.alice)

        self.client.post(f"/api/posts/{repost.id}/like/")

        self.assertTrue(Like.objects.filter(post=original, user=self.alice).exists())
        self.assertFalse(Like.objects.filter(post=repost).exists())

    def test_repost_toggles(self):
        original = Post.objects.create(user=self.alice, content="x")
        self.client.force_authenticate(self.bob)
        url = f"/api/posts/{original.id}/repost/"

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.filter(parent=original).count(), 1)

        self.client.post(url)
        self.assertEqual(Post.objects.filter(parent=original).count(), 0)


class FollowAndFeedTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", "alice@example.com", "pass12345")
        self.bob = User.objects.create_user("bob", "bob@example.com", "pass12345")
        self.carol = User.objects.create_user("carol", "carol@example.com", "pass12345")

    def test_follow_toggle(self):
        self.client.force_authenticate(self.alice)

        response = self.client.post("/api/follows/toggle/", {"user_id": self.bob.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Follow.objects.filter(follower=self.alice, following=self.bob).exists())

        response = self.client.post("/api/follows/toggle/", {"user_id": self.bob.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Follow.objects.filter(follower=self.alice, following=self.bob).exists())

    def test_feed_only_shows_followed_users(self):
        Follow.objects.create(follower=self.alice, following=self.bob)
        bobs_post = Post.objects.create(user=self.bob, content="from bob")
        Post.objects.create(user=self.carol, content="from carol")

        self.client.force_authenticate(self.alice)
        response = self.client.get("/api/posts/feed/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [post["id"] for post in response.data["results"]]
        self.assertEqual(ids, [bobs_post.id])