from django.contrib import admin
from .models import Product, LLMPrompt, LLMQueryResult


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["upc_code", "name", "brand", "has_image", "created_at"]
    search_fields = ["upc_code", "name", "brand"]
    list_filter = ["created_at"]
    readonly_fields = ["image_preview"]

    @admin.display(boolean=True, description="Has Image")
    def has_image(self, obj):
        return bool(obj.image_url)

    @admin.display(description="Image Preview")
    def image_preview(self, obj):
        if obj.image_url:
            from django.utils.html import format_html

            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" />',
                obj.image_url,
            )
        return "No image available"


@admin.register(LLMPrompt)
class LLMPromptAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "query_type",
        "schema_version",
        "is_active",
        "created_at",
        "updated_at",
    ]
    list_filter = ["query_type", "is_active", "created_at"]
    search_fields = ["name", "description", "prompt_template"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("Basic Information", {"fields": ("name", "query_type", "is_active")}),
        (
            "Prompt",
            {
                "fields": ("description", "prompt_template"),
                "description": "Use variables: {product_name}, {brand}, {upc_code}, {additional_data}",
            },
        ),
        (
            "Schema Configuration",
            {
                "fields": ("schema_version", "response_schema"),
                "classes": ("collapse",),
                "description": "Schema defines the expected JSON structure for responses",
            },
        ),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(LLMQueryResult)
class LLMQueryResultAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "prompt",
        "provider",
        "parse_strategy",
        "parse_attempts",
        "is_stale",
        "created_at",
    ]
    list_filter = [
        "provider",
        "parse_strategy",
        "is_stale",
        "created_at",
        "prompt__query_type",
    ]
    search_fields = ["product__name", "product__upc_code"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "query_input",
        "result",
        "metadata",
        "parse_strategy",
        "parse_attempts",
        "schema_version",
    ]
    date_hierarchy = "created_at"

    fieldsets = (
        ("Query Information", {"fields": ("product", "prompt", "provider")}),
        ("Request & Response", {"fields": ("query_input", "result", "metadata")}),
        (
            "Parsing Details",
            {"fields": ("parse_strategy", "parse_attempts", "schema_version")},
        ),
        ("Status", {"fields": ("is_stale",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = ["mark_as_stale", "mark_as_fresh"]

    @admin.action(
        description="Mark selected results as stale (will be refreshed on next request)"
    )
    def mark_as_stale(self, request, queryset):
        count = queryset.update(is_stale=True)
        self.message_user(request, f"{count} result(s) marked as stale.")

    @admin.action(description="Mark selected results as fresh")
    def mark_as_fresh(self, request, queryset):
        count = queryset.update(is_stale=False)
        self.message_user(request, f"{count} result(s) marked as fresh.")
