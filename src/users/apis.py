# DJANGO
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics, status, viewsets, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action


# LOCAL
from .models import (Profile, Followlist)
from .serializers import (UserSerializer,
                          UserLoginSerializer,
                          ProfileSerializer,
                          FollowListSerializer)

from core.request_responses import (FOLLOWING_EXISTS,
                                    REQUEST_CANCELED,
                                    PENDING_FOLLOW_REQUEST,
                                    FOLLOWING_SUCCESS,
                                    PENDING_APPROVAL,
                                    REQUEST_ACCEPTED)
User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        Profile.objects.create(user=user)


# class UserRegistrationView(GenericAPIView):
#     serializer_class = UserSerializer

#     def post(self, request):
#         serialzer = self.serializer_class(data=request.data)

#         if serialzer.is_valid():
#             user = serialzer.save()
#             self.perform_create(user)
#             return JsonResponse({'success': True}, status=201)
#         return JsonResponse({'success': False}, status=400)

#     def perform_create(self, user):
#         Profile.objects.create(user=user)


class UserLoginView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request):
        serializer = UserLoginSerializer(data=request.data)

        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = User.objects.filter(username=username).first()
            if user is None or not user.check_password(password):
                return Response({'detail': 'Invalid credentials'},
                                status=status.HTTP_401_UNAUTHORIZED)

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({'access_token': access_token, 'redirect_url': '/users/feed/'}, status=status.HTTP_200_OK)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__username']

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset()).exclude(user=request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET', 'PATCH'])
    def me(self, request):
        self.get_object = lambda: request.user.profile
        if request.method == "GET":
            return self.retrieve(request)
        elif request.method == 'PATCH':
            return self.partial_update(request)

    # @action(detail=False, methods=['GET', 'PATCH'])
    # def me(self, request, *args, **kwargs):
    #     if request.user.is_authenticated:
    #         if request.method == 'GET':
    #             print("get")
    #             user_profile = self.filter_queryset(self.queryset).get(user=request.user)
    #             serializer = ProfileSerializer(user_profile)
    #             return Response(serializer.data)
    #         elif request.method == 'PATCH':
    #             print("patch")
    #             self.get_object = lambda: request.user.profile
    #             return self.retrieve(request, *args, **kwargs)
    #             # user_profile = self.filter_queryset(self.queryset).get(user=request.user)
    #             # serializer = ProfileSerializer(user_profile, request.data, partial=True)
    #             # print(serializer)
    #             # if serializer.is_valid():
    #             #     print("if")
    #             #     serializer.save()
    #             #     return Response(serializer.data)
    #             # else:
    #             #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)               
    #     else:
    #         return Response({"detail": "User is not authenticated."}, status=status.HTTP_401_UNAUTHORIZED)


class FollowRequestView(APIView):

    def post(self, request):
        follower = request.user
        following_id = request.data.get('following_id')
        following = get_object_or_404(User, id=following_id)

        if follower == following:
            return Response({'detail': 'You cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            followlist = Followlist.objects.get(follower=follower, following=following)
            if followlist.reqstatus == 'accepted':
                return Response({'detail': FOLLOWING_EXISTS, 'reqstatus': 'accepted'}, status=status.HTTP_400_BAD_REQUEST)
            elif followlist.reqstatus == 'pending':
                action = request.data.get('action')
                if action == 'cancel':
                    followlist.delete()
                    return Response({'detail': REQUEST_CANCELED, 'reqstatus': 'rejected'}, status=status.HTTP_200_OK)
                return Response({'detail': PENDING_FOLLOW_REQUEST, 'reqstatus': 'pending'}, status=status.HTTP_400_BAD_REQUEST)
        except Followlist.DoesNotExist:
            pass

        if following.profile.public:
            Followlist.objects.create(follower=follower, following=following, reqstatus='accepted')
            return Response({'detail': FOLLOWING_SUCCESS, 'reqstatus': 'accepted'}, status=status.HTTP_201_CREATED)
        else:
            Followlist.objects.create(follower=follower, following=following, reqstatus='pending')
            action = request.data.get('action')
            if action == 'cancel':
                followlist.delete()
                return Response({'detail': REQUEST_CANCELED, 'reqstatus': 'rejected'}, status=status.HTTP_200_OK)
            return Response({'detail': PENDING_APPROVAL, 'reqstatus': 'pending'}, status=status.HTTP_201_CREATED)


class AcceptFollowRequest(viewsets.ModelViewSet):
    queryset = Followlist.objects.all()
    serializer_class = FollowListSerializer

    def create(self, request):
        following = request.user
        follower_id = request.data.get('follower_id')
        follower = get_object_or_404(User, id=follower_id)
        # try:
        #     follower = User.objects.get(id=follower_id)
        # except User.DoesNotExist:
        #     return Response({'detail': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)
        followlist = get_object_or_404(Followlist, follower=follower, following=following, reqstatus='pending')

        # try:
        #     followlist = Followlist.objects.get(follower=follower, following=following, reqstatus='pending')
        # except Followlist.DoesNotExist:
        #     return Response({'detail': REQUEST_NOT_FOUND }, status=status.HTTP_400_BAD_REQUEST)
        action = request.data.get('action')
        if action == 'accept' or action == 'Accept':
            followlist.reqstatus = 'accepted'
            followlist.save()
            return Response({'detail': REQUEST_ACCEPTED}, status=status.HTTP_200_OK)
        elif action == 'cancel' or action == 'Cancel':
            followlist.delete()
            return Response({'detail': REQUEST_CANCELED}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)


class Unfollow(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        user_to_unfollow = get_object_or_404(User, id=id)
        following = Followlist.objects.get(follower=request.user, following=user_to_unfollow, reqstatus='accepted')
        if following:
            following.delete()
            return Response({"detail": "You have unfollowed ."})

        return Response({"detail": "You were not following them"}, status=status.HTTP_404_NOT_FOUND) 
