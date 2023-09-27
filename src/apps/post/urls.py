from django.urls import path
from rest_framework.routers import DefaultRouter

# LOCAL
from .apis import (PostViewSet,
                   FeedAPIView)
from .views import (image_posting)

router = DefaultRouter()
router.register(r'posts', PostViewSet)

urlpatterns = [
    path('image-posting/', image_posting, name="image-posting"),

    # API
    path('feedAPI/', FeedAPIView.as_view(),)
]
