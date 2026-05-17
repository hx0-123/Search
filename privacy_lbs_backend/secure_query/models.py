from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class UserProfile(models.Model):
    """
    Store user basic information
    Extends Django's default User model with additional user-related information
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='User'
    )
    
    # User basic information
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Phone Number'
    )
    
    # User preferences
    default_text_weight = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='Default Text Weight',
        help_text='Text similarity weight, range 0-1'
    )
    
    default_distance_weight = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='Default Distance Weight',
        help_text='Distance similarity weight, range 0-1'
    )
    
    # User status
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        db_table = 'user_profile'
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - Profile"


class SecureQuery(models.Model):
    """
    Store encrypted query requests initiated by users
    Supports continuous queries and real-time location updates
    """
    
    QUERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Associated user
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='secure_queries',
        verbose_name='Query User'
    )
    
    # Query unique identifier
    query_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name='Query ID',
        help_text='Unique identifier for a query request'
    )
    
    # Encrypted query location (ciphertext)
    encrypted_location_x = models.TextField(
        verbose_name='Encrypted X Coordinate',
        help_text='X coordinate ciphertext using Paillier homomorphic encryption'
    )
    
    encrypted_location_y = models.TextField(
        verbose_name='Encrypted Y Coordinate',
        help_text='Y coordinate ciphertext using Paillier homomorphic encryption'
    )
    
    # Encrypted query keywords (ciphertext)
    encrypted_keywords = models.TextField(
        verbose_name='Encrypted Keywords',
        help_text='Encrypted keyword list stored in JSON format'
    )
    
    # Query parameters
    text_weight = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='Text Weight',
        help_text='Text similarity weight'
    )
    
    distance_weight = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='Distance Weight',
        help_text='Distance similarity weight'
    )
    
    top_k = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='Top-K Results',
        help_text='Return top K most similar results'
    )
    
    # Query status
    status = models.CharField(
        max_length=20,
        choices=QUERY_STATUS_CHOICES,
        default='pending',
        db_index=True,
        verbose_name='Query Status'
    )
    
    # Continuous query flag
    is_continuous = models.BooleanField(
        default=False,
        verbose_name='Is Continuous',
        help_text='Whether this is a continuous spatial query requiring real-time location updates'
    )
    
    # Query results (encrypted)
    encrypted_results = models.TextField(
        blank=True,
        null=True,
        verbose_name='Encrypted Results',
        help_text='Encrypted Top-K results stored in JSON format'
    )
    
    # Query metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Query Metadata',
        help_text='Store additional query-related information like query time, processing nodes, etc.'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Completed At'
    )
    
    class Meta:
        verbose_name = 'Secure Query'
        verbose_name_plural = 'Secure Queries'
        db_table = 'secure_query'
        indexes = [
            models.Index(fields=['user', 'status', 'created_at']),
            models.Index(fields=['query_id']),
            models.Index(fields=['is_continuous', 'status']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Query {self.query_id} by {self.user.username} - {self.get_status_display()}"
    
    def get_encrypted_keywords_list(self):
        """Parse encrypted keywords list"""
        try:
            return json.loads(self.encrypted_keywords)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_encrypted_keywords_list(self, keywords_list):
        """Set encrypted keywords list"""
        self.encrypted_keywords = json.dumps(keywords_list, ensure_ascii=False)


class QueryLog(models.Model):
    """
    Query log for recording query history and analysis
    """
    query = models.ForeignKey(
        SecureQuery,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='Query'
    )
    
    log_type = models.CharField(
        max_length=50,
        verbose_name='Log Type',
        help_text='e.g.: query_received, index_search, fog_computation, result_returned'
    )
    
    message = models.TextField(
        verbose_name='Log Message'
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Log Metadata'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Created At'
    )
    
    class Meta:
        verbose_name = 'Query Log'
        verbose_name_plural = 'Query Logs'
        db_table = 'query_log'
        indexes = [
            models.Index(fields=['query', 'created_at']),
            models.Index(fields=['log_type', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Log for {self.query.query_id} - {self.log_type}"
