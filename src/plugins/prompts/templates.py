# src/plugins/prompts/templates.py
class PromptTemplateLoader:
    def load_template(self, template_path: str) -> PromptTemplate
    def validate_template(self, template: PromptTemplate) -> bool