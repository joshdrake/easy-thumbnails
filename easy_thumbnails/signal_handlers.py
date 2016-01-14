from django.db.models.fields.files import FileField

from easy_thumbnails import signals


def find_uncommitted_filefields(sender, instance, **kwargs):
    """
    A pre_save signal handler which attaches an attribute to the model instance
    containing all uncommitted ``FileField``s, which can then be used by the
    :func:`signal_updated_filefields` post_save handler.
    """
    uncommitted = instance._uncommitted_filefields = set()
    # check all fields on the model for uncommitted ``FileField`` instances -
    # the '_committed' flag is *only* set to ``False`` occurs when directly setting
    # the model field attribute to an instance of ``File``
    for field in sender._meta.fields:
        if isinstance(field, FileField):
            if not getattr(instance, field.name)._committed:
                uncommitted.add(field.name)


def signal_updated_filefields(sender, instance, **kwargs):
    """
    A post_save signal handler which sends a signal for each ``FileField`` that
    was updated this save.
    """
    # grab fields added when checking for uncommitted ``FileField`` instances
    uncommitted = getattr(instance, '_uncommitted_filefields', set())
    # we'll emit the signal for any fields explicitly declared in 'update_fields'
    updated = kwargs.get('update_fields', None) or set()
    for field_name in uncommitted | updated:
        fieldfile = getattr(instance, field_name)
        # Don't send the signal for deleted files.
        if fieldfile:
            signals.saved_file.send_robust(sender=sender, fieldfile=fieldfile)


def generate_aliases(fieldfile, **kwargs):
    """
    A saved_file signal handler which generates thumbnails for all field,
    model, and app specific aliases matching the saved file's field.
    """
    # Avoids circular import.
    from easy_thumbnails.files import generate_all_aliases
    generate_all_aliases(fieldfile, include_global=False)


def generate_aliases_global(fieldfile, **kwargs):
    """
    A saved_file signal handler which generates thumbnails for all field,
    model, and app specific aliases matching the saved file's field, also
    generating thumbnails for each project-wide alias.
    """
    # Avoids circular import.
    from easy_thumbnails.files import generate_all_aliases
    generate_all_aliases(fieldfile, include_global=True)
