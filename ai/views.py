import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from materials.models import Material
from .models import AIInteraction
from .services.prompt_builder import build_lesson_prompt
from .providers.mock_provider import MockProvider

from django_ratelimit.decorators import ratelimit

@csrf_exempt
@login_required
@ratelimit(key='user', rate='10/m', method='POST', block=True)
def ask_ai(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST allowed"}, status=405)
        
    try:
        data = json.loads(request.body)
        material_id = data.get('material_id')
        action = data.get('action') # e.g. 'Summarize Lesson'
        user_prompt = data.get('prompt', '')
        
        if len(user_prompt) > 2000:
            return JsonResponse({"error": "Prompt exceeds maximum length of 2000 characters"}, status=400)
            
        material = Material.objects.get(id=material_id)
        profile = request.user.profile
        
        # 1. Build Contextual Prompt
        sys_prompt, final_prompt = build_lesson_prompt(material, action, user_prompt, profile)
        
        # 2. Query Provider (Mock for now, easy to swap based on settings)
        provider = MockProvider()
        response_text = provider.generate(final_prompt, system_message=sys_prompt)
        
        # 3. Log Interaction
        AIInteraction.objects.create(
            user=request.user,
            material=material,
            action=action,
            prompt=final_prompt,
            response=response_text,
            provider="mock"
        )
        
        return JsonResponse({"response": response_text})
        
    except Material.DoesNotExist:
        return JsonResponse({"error": "Material not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
