from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import json


class DataOwner(models.Model):
    """
    Data Owner Information
    Manages data upload, encryption and index building
    """
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='data_owners',
        verbose_name='Associated User',
        null=True,
        blank=True,
    )

    # Data owner identifier
    owner_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name='Owner ID'
    )

    # Public key information (for homomorphic encryption)
    public_key = models.TextField(
        verbose_name='Public Key',
        help_text='Paillier homomorphic encryption public key for data encryption'
    )

    # Data statistics
    total_objects = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Total Objects'
    )

    encrypted_objects = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Encrypted Objects'
    )

    # Index build status
    index_built = models.BooleanField(
        default=False,
        verbose_name='Index Built',
        help_text='Whether KASTree index has been built'
    )

    index_version = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        verbose_name='Index Version',
        help_text='Index version number for version management'
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
        verbose_name = 'Data Owner'
        verbose_name_plural = 'Data Owners'
        db_table = 'data_owner'
        indexes = [
            models.Index(fields=['owner_id']),
            models.Index(fields=['index_built']),
        ]

    def __str__(self):
        return f"DataOwner {self.owner_id} - {self.user.username}"


class EncryptedSpatialObject(models.Model):
    """
    Stores encrypted spatial text objects from data owners
    Contains encrypted locations, encrypted keyword collections, etc.
    """

    # Associated data owner
    data_owner = models.ForeignKey(
        DataOwner,
        on_delete=models.CASCADE,
        related_name='spatial_objects',
        verbose_name='Data Owner'
    )

    # Object unique identifier
    object_id = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name='Object ID',
        help_text='Unique identifier for spatial object'
    )

    # Original location information (optional, for debugging, should be removed in production)
    original_x = models.FloatField(
        blank=True,
        null=True,
        verbose_name='Original X Coordinate',
        help_text='Only for development debugging, should be removed in production'
    )

    original_y = models.FloatField(
        blank=True,
        null=True,
        verbose_name='Original Y Coordinate',
        help_text='Only for development debugging, should be removed in production'
    )

    # Encrypted location information (ciphertext)
    encrypted_location_x = models.TextField(
        verbose_name='Encrypted X Coordinate',
        help_text='X coordinate ciphertext using Paillier homomorphic encryption'
    )

    encrypted_location_y = models.TextField(
        verbose_name='Encrypted Y Coordinate',
        help_text='Y coordinate ciphertext using Paillier homomorphic encryption'
    )

    # Encrypted keyword collection (ciphertext)
    encrypted_keywords = models.TextField(
        verbose_name='Encrypted Keyword Collection',
        help_text='JSON format encrypted keyword list'
    )

    # Encrypted name (ciphertext)
    encrypted_name = models.TextField(
        blank=True,
        null=True,
        verbose_name='Encrypted Name',
        help_text='POI readable name ciphertext using Paillier homomorphic encryption'
    )

    # Object document information (encrypted)
    encrypted_document = models.TextField(
        blank=True,
        null=True,
        verbose_name='Encrypted Document',
        help_text='Encrypted document content or identifier'
    )

    # Object metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Object Metadata',
        help_text='Additional object information such as category, tags, etc.'
    )

    # KTree node association information
    ktree_node_path = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        verbose_name='KTree Node Path',
        help_text='Object path in KTree for index retrieval'
    )

    ktree_region = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='KTree Region Number',
        help_text='KTree region number the object belongs to (0-3)'
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

    class Meta:
        verbose_name = 'Encrypted Spatial Object'
        verbose_name_plural = 'Encrypted Spatial Objects'
        db_table = 'encrypted_spatial_object'
        indexes = [
            models.Index(fields=['data_owner', 'object_id']),
            models.Index(fields=['ktree_region', 'ktree_node_path']),
            models.Index(fields=['created_at']),
        ]
        # Ensure object_id is unique for the same data owner
        unique_together = [['data_owner', 'object_id']]

    def __str__(self):
        return f"Object {self.object_id} by {self.data_owner.owner_id}"

    def get_encrypted_keywords_list(self):
        """Parse encrypted keyword list"""
        try:
            return json.loads(self.encrypted_keywords)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_encrypted_keywords_list(self, keywords_list):
        """Set encrypted keyword list"""
        self.encrypted_keywords = json.dumps(keywords_list, ensure_ascii=False)


class KeyPair(models.Model):
    """
    Paillier Key Pair Persistence
    Public key stored in plaintext, private key encrypted then stored (stored directly in demo environment)
    """
    KEY_SIZE_CHOICES = [
        (512,  '512 bit'),
        (1024, '1024 bit'),
        (2048, '2048 bit'),
    ]

    key_size = models.IntegerField(
        choices=KEY_SIZE_CHOICES,
        default=1024,
        verbose_name='Key Size (bits)'
    )

    public_key = models.TextField(
        verbose_name='Public Key (Serialized)',
        help_text='Base64 encoded Paillier public key'
    )

    private_key = models.TextField(
        verbose_name='Private Key (Serialized)',
        help_text='Base64 encoded Paillier private key (stored in demo environment)'
    )

    # First 16 characters of public key n, for quick verification
    public_key_digest = models.CharField(
        max_length=32,
        verbose_name='Public Key Digest',
        db_index=True
    )

    gen_time_ms = models.IntegerField(
        default=0,
        verbose_name='Generation Time (ms)'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Currently Active Key'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )

    class Meta:
        verbose_name = 'Paillier Key Pair'
        verbose_name_plural = 'Paillier Key Pairs'
        db_table = 'keypair'
        ordering = ['-created_at']

    def __str__(self):
        return f"KeyPair {self.key_size}-bit  digest={self.public_key_digest}  active={self.is_active}"


class IndexMetadata(models.Model):
    """
    KASTree Index Metadata
    Since KTree and AssetTree structures are complex and involve many ciphertext operations,
    actual index data is stored in Redis or Cassandra,
    this model only stores index metadata information
    """

    # Associated data owner
    data_owner = models.OneToOneField(
        DataOwner,
        on_delete=models.CASCADE,
        related_name='index_metadata',
        verbose_name='Data Owner'
    )

    # KTree metadata
    ktree_depth = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='KTree Depth',
        help_text='KTree depth (height)'
    )

    ktree_node_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='KTree Node Count'
    )

    ktree_leaf_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='KTree Leaf Node Count'
    )

    # Spatial domain information
    spatial_domain_x_min = models.FloatField(
        verbose_name='X Axis Minimum',
        help_text='X axis minimum of data spatial domain'
    )

    spatial_domain_x_max = models.FloatField(
        verbose_name='X Axis Maximum',
        help_text='X axis maximum of data spatial domain'
    )

    spatial_domain_y_min = models.FloatField(
        verbose_name='Y Axis Minimum',
        help_text='Y axis minimum of data spatial domain'
    )

    spatial_domain_y_max = models.FloatField(
        verbose_name='Y Axis Maximum',
        help_text='Y axis maximum of data spatial domain'
    )

    # AssetTree metadata
    assettree_size = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='AssetTree Size',
        help_text='Number of nodes in AssetTree'
    )

    # Index storage location
    index_storage_type = models.CharField(
        max_length=20,
        choices=[
            ('redis', 'Redis'),
            ('cassandra', 'Cassandra'),
            ('file', 'File System'),
            ('memory', 'Memory'),
        ],
        default='redis',
        verbose_name='Index Storage Type'
    )

    index_storage_path = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        verbose_name='Index Storage Path',
        help_text='Path or key name of index in storage system'
    )

    # Index build information
    build_status = models.CharField(
        max_length=20,
        choices=[
            ('not_started', 'Not Started'),
            ('building', 'Building'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='not_started',
        verbose_name='Build Status'
    )

    build_started_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Build Started At'
    )

    build_completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Build Completed At'
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
        verbose_name = 'Index Metadata'
        verbose_name_plural = 'Index Metadata'
        db_table = 'index_metadata'

    def __str__(self):
        return f"IndexMetadata for {self.data_owner.owner_id} - {self.get_build_status_display()}"
