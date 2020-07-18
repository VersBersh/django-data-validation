.. _admin:

Setting up the Admin
====================

Data Validation Summary
-----------------------

Once you have run ``./manage.py run_data_validation`` the results can be viewed in the django admin. The only set up required is to run

.. code-block:: bash

    ./manage.py collectstatic

To copy static assets to your `$STATIC_ROOT` directory


Admin Mixin
-----------

If you want your objects validated when they are saved in the django-admin form then you can add the ``data_validation.admin.DataValidationMixin`` to your ModelAdmins. You must remember to add the mixin before ``admin.ModelAdmin``. For instance

.. code-block:: python

    from data_validation.admin import DataValidationMixin
    from django.contrib import admin

    @admin.register(YourModel)
    class YouModelAdmin(DataValidationMixin, admin.ModelAdmin):
        pass


If you are using a custom admin template (i.e. you set the property ``change_form_template`` or ``add_form_template`` on your model admin) you must add the following line to your template to render the validation result inlines.

.. code-block:: jinja

    <form>
    ...
    {# this line must be between the <form> tags (ideally near the top) #}
    {% include "datavalidation/admin_mixin/datavalidation_inline.html" %}

    </form>

