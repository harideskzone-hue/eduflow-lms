import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from paths.models import CareerTrack, LearningPath, Skill, LearningPathCourse
from courses.models import Course

def seed():
    track, _ = CareerTrack.objects.get_or_create(title="Full Stack Developer", slug="full-stack-developer", description="Become a full stack web developer.")
    path, _ = LearningPath.objects.get_or_create(title="Full Stack Developer", slug="full-stack", career_track=track, difficulty="Intermediate", estimated_hours=120, career_outcome="Full Stack Web Developer")
    
    python, _ = Skill.objects.get_or_create(name="Python", slug="python", category="Backend")
    django_skill, _ = Skill.objects.get_or_create(name="Django", slug="django", category="Backend")
    react, _ = Skill.objects.get_or_create(name="React", slug="react", category="Frontend")
    html, _ = Skill.objects.get_or_create(name="HTML & CSS", slug="html-css", category="Frontend")

    # Assuming there are some courses in DB
    courses = list(Course.objects.all()[:3])
    
    if courses:
        courses[0].skills.add(python, html)
        if len(courses) > 1:
            courses[1].skills.add(django_skill)
        if len(courses) > 2:
            courses[2].skills.add(react)
            
        for i, c in enumerate(courses):
            LearningPathCourse.objects.get_or_create(
                learning_path=path,
                course=c,
                order=i,
                required=True
            )
            
    print("Seeded paths and skills successfully.")

if __name__ == "__main__":
    seed()
