from rest_framework import serializers
from django.contrib.auth import authenticate,get_user_model
import base64
import uuid
from django.core.files.base import ContentFile

from Account.models import User ,StudentProfile,TeacherProfile,StaffProfile,ParentProfile
from schoolApp.models import Class
User  =  get_user_model()
# ---------------------------
# Registration Serializer
# ---------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['id','username',  'email', 'password', 'confirm_password', 'role']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')

        if User.objects.filter(email=validated_data['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists."})
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'student')
        )
        return user
    
# Login Serializer
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        data["user"] = user
        return data

    
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        # Check old password
        if not user.check_password(old_password):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})

        # Check new passwords match
        if new_password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        # Optionally add password strength validation
        if len(new_password) < 8:
            raise serializers.ValidationError({"new_password": "Password must be at least 8 characters."})

        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user    
    
class TeacherProfileSerializer(serializers.ModelSerializer):
    # Accept base64 or dict for files/profile pic from frontend
    aadhaar_doc = serializers.JSONField(write_only=True, required=False, allow_null=True)
    experience_doc = serializers.JSONField(write_only=True, required=False, allow_null=True)
    # frontend may send profile_picture as {name: string, data: base64string}
    profile_picture = serializers.JSONField(write_only=True, required=False, allow_null=True)
    # Expose a read-only URL for the saved profile picture so frontend can display it
    profile_picture_url = serializers.SerializerMethodField(read_only=True)

    class_teacher_display = serializers.CharField(source='class_teacher_of.name', read_only=True)

    class Meta:
        model = TeacherProfile
        fields = "__all__"
        read_only_fields = ['staff_id', 'updated_at']

    def _contentfile_from_base64(self, data, default_name):
        if not data:
            return None
        # data could be a dict {name, data} or a raw base64 string
        if isinstance(data, dict):
            name = data.get('name') or default_name
            b64 = data.get('data') or data.get('url')
        else:
            name = default_name
            b64 = data

        if not b64:
            return None

        # if data URI, strip header
        if isinstance(b64, str) and b64.startswith('data:'):
            try:
                header, b64 = b64.split(',', 1)
            except ValueError:
                return None

        try:
            decoded = base64.b64decode(b64)
        except Exception:
            return None

        filename = f"{uuid.uuid4().hex}_{name}"
        return ContentFile(decoded, name=filename)

    def create(self, validated_data):
        aadhaar_b64 = validated_data.pop('aadhaar_doc', None)
        exp_b64 = validated_data.pop('experience_doc', None)
        profile_pic = validated_data.pop('profile_picture', None)

        # Create instance without file fields first
        instance = super().create(validated_data)

        # Attach files if provided (decoded from base64)
        if profile_pic:
            f = self._contentfile_from_base64(profile_pic, profile_pic.get('name') if isinstance(profile_pic, dict) else 'profile.jpg')
            if f:
                instance.profile_picture.save(f.name, f, save=True)

        if aadhaar_b64:
            f = self._contentfile_from_base64(aadhaar_b64, 'aadhaar')
            if f:
                instance.aadhaar_doc.save(f.name, f, save=True)

        if exp_b64:
            f = self._contentfile_from_base64(exp_b64, 'experience')
            if f:
                instance.experience_doc.save(f.name, f, save=True)

        return instance

    def update(self, instance, validated_data):
        aadhaar_b64 = validated_data.pop('aadhaar_doc', None)
        exp_b64 = validated_data.pop('experience_doc', None)
        profile_pic = validated_data.pop('profile_picture', None)

        # Update regular fields
        instance = super().update(instance, validated_data)

        # If new files provided, replace existing ones
        if profile_pic:
            f = self._contentfile_from_base64(profile_pic, profile_pic.get('name') if isinstance(profile_pic, dict) else 'profile.jpg')
            if f:
                instance.profile_picture.save(f.name, f, save=True)

        if aadhaar_b64:
            f = self._contentfile_from_base64(aadhaar_b64, 'aadhaar')
            if f:
                instance.aadhaar_doc.save(f.name, f, save=True)

        if exp_b64:
            f = self._contentfile_from_base64(exp_b64, 'experience')
            if f:
                instance.experience_doc.save(f.name, f, save=True)

        return instance

    def get_profile_picture_url(self, obj):
        try:
            if not obj or not getattr(obj, 'profile_picture'):
                return None
            url = obj.profile_picture.url
            request = self.context.get('request') if hasattr(self, 'context') else None
            if request:
                return request.build_absolute_uri(url)
            return url
        except Exception:
            return None
    
    """def validate_aadhaar_number(self, value):
       
        if len(value) != 12 or not value.isdigit():
            raise serializers.ValidationError("Aadhaar number must be exactly 12 digits.")
        return value"""

class StaffProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = StaffProfile
        fields = "__all__"
class ParentProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ParentProfile
        fields = "__all__"
         
class StudentProfileSerializer(serializers.ModelSerializer):
    # Make `class_name` writable (accept class PK) and also expose a read-only
    # human-friendly label `class_display` for UI usage.
    class_name = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all())
    class_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = StudentProfile
        fields = "__all__"
        read_only_fields = ['enrollment_no', 'created_at']

    def get_class_display(self, obj):
        try:
            return f"{obj.class_name.class_name}-{obj.class_name.section}"
        except Exception:
            return None
