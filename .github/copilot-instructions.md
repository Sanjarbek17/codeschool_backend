# GitHub Copilot Instructions for Django Framework Development

## Project Overview
This is a Django REST API backend project with the following structure:
- **Django Framework**: Web framework for rapid development
- **Django REST Framework**: For building RESTful APIs
- **Django CORS Headers**: For handling Cross-Origin Resource Sharing
- **SQLite/PostgreSQL**: Database backend
- **Memory Bank MCP**: **CRITICAL** - Always use Memory Bank MCP for persistent storage and retrieval of project information, code snippets, and documentation

## Memory Bank MCP Integration

### **MOST IMPORTANT**: Memory Bank Usage
- **ALWAYS** use Memory Bank MCP for storing and retrieving project-related information
- Store code patterns, configurations, and project decisions in Memory Bank
- Retrieve previous implementations and solutions from Memory Bank before writing new code
- Use Memory Bank to maintain consistency across the project
- Document all major code changes and architectural decisions in Memory Bank

### Memory Bank Best Practices
- Create dedicated files for different aspects (models, views, configurations, etc.)
- Use descriptive file names in Memory Bank (e.g., "django_auth_patterns.md", "api_endpoints.md")
- Update Memory Bank entries when making significant changes
- Reference Memory Bank entries when implementing similar features
- Store reusable code snippets and configurations in Memory Bank

```python
# Example: Always check Memory Bank before implementing new features
# 1. Search Memory Bank for similar implementations
# 2. Retrieve existing patterns and configurations
# 3. Adapt and extend existing solutions
# 4. Update Memory Bank with new implementations
```

## Code Style and Conventions

### Python/Django Standards
- Follow PEP 8 style guidelines
- Use descriptive variable and function names
- Maintain consistent indentation (4 spaces)
- Use docstrings for classes and functions
- Prefer list comprehensions over loops when appropriate

### Django-Specific Conventions
- Use Django's naming conventions for models, views, and URLs
- Follow Django's project structure with apps for modular organization
- Use Django's built-in authentication and permissions system
- Implement proper error handling with Django's exception classes

## Models Guidelines

### Model Design
- Use descriptive model names in singular form (e.g., `User`, `Article`, `Comment`)
- Add `__str__` methods to all models for better admin representation
- Use appropriate field types with proper constraints
- Add related_name for ForeignKey and ManyToMany relationships
- Include created_at and updated_at fields using Django's auto_now and auto_now_add

```python
# Example model structure
class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
```

### Field Best Practices
- Use `blank=True, null=True` only when necessary
- Set appropriate `max_length` for CharField
- Use `choices` for predefined options
- Add `help_text` for complex fields

## Views and API Design

### Django REST Framework Views
- Use ViewSets for CRUD operations
- Implement proper serializers for data validation
- Use appropriate permissions and authentication
- Handle exceptions gracefully with proper HTTP status codes

```python
# Example ViewSet structure
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        # Add filtering logic if needed
        return super().get_queryset()
```

### Serializers
- Use ModelSerializer when possible
- Validate data in serializer methods
- Handle nested relationships appropriately
- Use `read_only_fields` for fields that shouldn't be modified

## URL Configuration

### URL Patterns
- Use descriptive URL names
- Group related URLs in app-specific url files
- Use namespaces for app URLs
- Follow RESTful conventions for API endpoints

```python
# Example URL patterns
urlpatterns = [
    path('api/articles/', ArticleListCreateView.as_view(), name='article-list'),
    path('api/articles/<int:pk>/', ArticleDetailView.as_view(), name='article-detail'),
]
```

## Database and Migrations

### Migration Best Practices
- Create meaningful migration names
- Test migrations on development data
- Use data migrations for complex changes
- Avoid editing migration files manually

### Database Queries
- Use select_related() and prefetch_related() to optimize queries
- Avoid N+1 query problems
- Use F() expressions for atomic database operations
- Implement database indexes for frequently queried fields

## Security Guidelines

### Authentication and Authorization
- Use Django's built-in authentication system with simple token authentication
- Implement Django REST Framework's TokenAuthentication for API access
- Use proper permission classes (IsAuthenticated, IsAuthenticatedOrReadOnly, etc.)
- Generate tokens for users upon registration or login
- Include 'rest_framework.authtoken' in INSTALLED_APPS
- Validate user input thoroughly
- Use HTTPS in production settings

```python
# Example token authentication setup in settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Example token creation in views
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})
```

### Data Protection
- Never store sensitive data in plain text
- Use Django's built-in CSRF protection
- Validate and sanitize all user inputs

## Testing Guidelines

### Test Structure
- Write unit tests for models, views, and utility functions
- Use Django's TestCase for database-related tests
- Mock external dependencies
- Test both success and failure scenarios

```python
# Example test structure
class ArticleModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser')
        
    def test_article_creation(self):
        article = Article.objects.create(
            title='Test Article',
            content='Test content',
            author=self.user
        )
        self.assertEqual(article.title, 'Test Article')
```

## Settings Configuration

### Environment-Specific Settings
- Use environment variables for sensitive configuration
- Separate settings for development, staging, and production
- Use Django's built-in settings module structure
- Keep SECRET_KEY and database credentials secure

### Required Environment Variables
- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (True/False)
- `DATABASE_URL`: Database connection string
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

## Performance Optimization

### Database Optimization
- Use select_related() and prefetch_related() to optimize queries
- Avoid N+1 query problems
- Use F() expressions for atomic database operations
- Implement database indexes for frequently queried fields

## Error Handling

### Exception Handling
- Use Django's built-in exception classes
- Implement custom exception handlers for API responses
- Log errors appropriately for debugging
- Return meaningful error messages to clients

```python
# Example error handling
try:
    article = Article.objects.get(id=article_id)
except Article.DoesNotExist:
    return Response(
        {'error': 'Article not found'}, 
        status=status.HTTP_404_NOT_FOUND
    )
```

## Development Workflow

### Code Organization
- Keep views, models, and serializers in separate files for large apps
- Use Django's app structure for modular development
- Implement proper imports and avoid circular dependencies
- Use Django's built-in management commands

## Deployment Considerations

### Production Settings
- Set DEBUG=False in production
- Use environment variables for configuration
- Implement proper logging
- Use HTTPS and secure headers
- Set up proper static file serving

---

## Copilot-Specific Instructions

When generating code suggestions:
1. **ALWAYS use Memory Bank MCP first** - Check Memory Bank for existing patterns and solutions before creating new code
2. **Store code in Memory Bank** - Save new implementations, patterns, and configurations to Memory Bank for future reference
3. **Follow Django conventions** and the project's existing patterns
4. **Include proper imports** for Django modules and dependencies
5. **Add appropriate error handling** and validation
6. **Generate complete code blocks** with proper context
7. **Include docstrings and comments** for complex logic
8. **Suggest performance optimizations** when applicable
9. **Consider security implications** in all code suggestions
10. **Use type hints** where appropriate for better code clarity
11. **Update Memory Bank** after implementing new features or making significant changes

### Memory Bank Workflow for Copilot:
1. Before implementing any feature, search Memory Bank for similar implementations
2. Retrieve and adapt existing patterns from Memory Bank
3. Implement the feature using established patterns
4. Document the new implementation in Memory Bank
5. Reference Memory Bank entries in code comments when appropriate

Remember to always consider the existing codebase structure and maintain consistency with established patterns in this Django project.

**CRITICAL REMINDER**: Always use Memory Bank MCP for persistent storage and retrieval of project information, code snippets, and documentation to ensure consistency and avoid reinventing solutions.
