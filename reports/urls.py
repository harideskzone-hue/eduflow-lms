from django.urls import path

from .views import reports_dashboard
from .exporters.csv import (
    export_enrollments_csv,
    export_quiz_results_csv,
    export_certificates_csv,
    export_audit_logs_csv,
)
from .exporters.excel import (
    export_enrollments_excel,
    export_quiz_results_excel,
    export_certificates_excel,
    export_audit_logs_excel,
)
from .exporters.pdf import (
    export_audit_summary_pdf,
    export_certificate_statistics_pdf,
    export_student_progress_pdf,
    export_course_analytics_pdf,
)

urlpatterns = [
    path("",                                          reports_dashboard,               name="reports_dashboard"),
    # CSV
    path("csv/enrollments/",                          export_enrollments_csv,          name="export_enrollments_csv"),
    path("csv/quizzes/",                              export_quiz_results_csv,         name="export_quiz_results_csv"),
    path("csv/certificates/",                         export_certificates_csv,         name="export_certificates_csv"),
    path("csv/audit/",                                export_audit_logs_csv,           name="export_audit_logs_csv"),
    # Excel
    path("excel/enrollments/",                        export_enrollments_excel,        name="export_enrollments_excel"),
    path("excel/quizzes/",                            export_quiz_results_excel,       name="export_quiz_results_excel"),
    path("excel/certificates/",                       export_certificates_excel,       name="export_certificates_excel"),
    path("excel/audit/",                              export_audit_logs_excel,         name="export_audit_logs_excel"),
    # PDF
    path("pdf/audit/",                                export_audit_summary_pdf,        name="export_audit_summary_pdf"),
    path("pdf/certificates/",                         export_certificate_statistics_pdf, name="export_certificate_statistics_pdf"),
    path("pdf/student-progress/<int:student_id>/",    export_student_progress_pdf,     name="export_student_progress_pdf"),
    path("pdf/course-analytics/<int:course_id>/",     export_course_analytics_pdf,     name="export_course_analytics_pdf"),
]
