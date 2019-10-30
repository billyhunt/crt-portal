from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required

from formtools.wizard.views import SessionWizardView

from .models import Report, ProtectedClass
from .model_variables import PROTECTED_CLASS_CODES

import logging

logger = logging.getLogger(__name__)


@login_required
def IndexView(request):
    latest_reports = Report.objects.order_by('-create_date')
    data = []
    # formatting protected class
    for report in latest_reports:
        reports = []
        for p_class in report.protected_class.all().order_by('form_order'):
            if p_class.protected_class is not None:
                code = PROTECTED_CLASS_CODES.get(p_class.protected_class, p_class.protected_class)
                if code is not 'Other':
                    reports.append(code)
                # If this code is other but there is no other_class description, we want it to say "Other". If there is an other_class that will take the place of "Other"
                elif report.other_class is None:
                    reports.append(code)
        if report.other_class:
            reports.append(report.other_class)
        if len(reports) > 3:
            reports = reports[:3]
            reports[2] = f'{reports[2]}...'
        data.append([p_class, reports])

    return render_to_response('forms/index.html', {'data_dict': data})


TEMPLATES = [
    # Contact
    'forms/report_grouped_questions.html',
    # Protected Class
    'forms/report_class.html',
    # Details
    'forms/report_details.html',
]


class CRTReportWizard(SessionWizardView):
    """Once all the sub-forms are submitted this class will clean data and save."""
    def get_template_names(self):
        return [TEMPLATES[int(self.steps.current)]]

    def get_context_data(self, form, **kwargs):
        context = super(CRTReportWizard, self).get_context_data(form=form, **kwargs)

        # This name appears in the progress bar wizard
        ordered_step_names = [
            'Contact',
            'Protected Class',
            'Details',
            # 'What Happened',
            # 'Where',
            # 'Who',
        ]
        current_step_name = ordered_step_names[int(self.steps.current)]

        # This title appears in large font above the question elements
        ordered_step_titles = [
            'Contact',
            'Please provide details on what happened',
            'Details'
        ]
        current_step_title = ordered_step_titles[int(self.steps.current)]

        context.update({
            'ordered_step_names': ordered_step_names,
            'current_step_title': current_step_title,
            'current_step_name': current_step_name
        })

        if current_step_name == 'Details':
            context.update({
                'page_subtitle': 'Please describe what happened in your own words',
                'page_note': 'Continued'
            })

        return context

    def done(self, form_list, form_dict, **kwargs):
        form_data_dict = self.get_all_cleaned_data()
        m2mfield = form_data_dict.pop('protected_class')
        r = Report.objects.create(**form_data_dict)
        r.save()

        # Many to many fields need to be added or updated to the main model, with a related manager such as add() or update()
        for protected in m2mfield:
            p = ProtectedClass.objects.get(protected_class=protected)
            r.protected_class.add(p)

        r.save()
        # adding this back for the save page results
        form_data_dict['protected_class'] = m2mfield.values()

        return render_to_response('forms/confirmation.html', {'data_dict': form_data_dict})
