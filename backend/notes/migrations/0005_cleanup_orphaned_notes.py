# Generated manually

from django.db import migrations

def cleanup_orphaned_notes(apps, schema_editor):
    """
    Clean up any notes that don't have a unit assigned.
    These notes were likely created before the unit structure was implemented.
    """
    Note = apps.get_model('notes', 'Note')
    
    # Delete notes without units (orphaned notes)
    orphaned_notes = Note.objects.filter(unit__isnull=True)
    print(f"Deleting {orphaned_notes.count()} orphaned notes without units")
    orphaned_notes.delete()
    
    # Also delete notes that still have the old tab field but no unit
    # (these are from before the migration to units)
    old_notes = Note.objects.filter(tab__isnull=False, unit__isnull=True)
    print(f"Deleting {old_notes.count()} old notes with tab but no unit")
    old_notes.delete()

def reverse_cleanup_orphaned_notes(apps, schema_editor):
    """
    This migration cannot be reversed as it deletes data.
    """
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0004_alter_note_tab_unit_note_unit'),
    ]

    operations = [
        migrations.RunPython(cleanup_orphaned_notes, reverse_cleanup_orphaned_notes),
    ] 