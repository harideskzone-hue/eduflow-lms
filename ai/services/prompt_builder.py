def build_lesson_prompt(lesson, action, user_prompt, profile):
    """
    Constructs a highly contextual prompt using the learner's identity
    and the lesson's exact content.
    """
    
    system_prompt = (
        "You are the EduFlow Contextual AI Assistant. "
        "Your goal is to help the learner understand the material. "
        "Keep responses concise, educational, and formatting in clean markdown."
    )
    
    context = (
        f"--- LEARNER CONTEXT ---\n"
        f"Name: {profile.user.username}\n"
        f"Goal: {profile.career_goal or 'Continuous Learning'}\n"
        f"Level: {profile.level}\n"
        f"-----------------------\n\n"
        f"--- LESSON CONTEXT ---\n"
        f"Course: {lesson.course.title}\n"
        f"Lesson: {lesson.title}\n"
        f"Content:\n{lesson.content}\n"
        f"-----------------------\n\n"
    )
    
    action_prompts = {
        "Summarize Lesson": "Please provide a highly concise summary of the lesson content above.",
        "Explain This Concept": f"Please explain the following concept from the lesson: '{user_prompt}'",
        "Generate Notes": "Please generate structured study notes based on this lesson.",
        "Quiz Me": "Please ask me 3 multiple choice questions to test my knowledge on this lesson.",
        "Ask About This Lesson": f"The learner asks: {user_prompt}"
    }
    
    final_prompt = context + action_prompts.get(action, f"User asked: {user_prompt}")
    
    return system_prompt, final_prompt
