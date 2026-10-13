from controllers.common import get_or_404
from controllers.validators import validate_category
from models.category import Category

CATEGORY_NOT_FOUND = 'Categoria não encontrada'


class CategoryController:
    def list_categories(self):
        result = []
        for category, task_count in Category.all_with_task_counts():
            data = category.to_dict()
            data['task_count'] = task_count
            result.append(data)
        return result, 200

    def create_category(self, data):
        category = Category(**validate_category(data, partial=False)).save()
        return category.to_dict(), 201

    def update_category(self, category_id, data):
        category = get_or_404(Category, category_id, CATEGORY_NOT_FOUND)
        for key, value in validate_category(data, partial=True).items():
            setattr(category, key, value)
        category.save()
        return category.to_dict(), 200

    def delete_category(self, category_id):
        category = get_or_404(Category, category_id, CATEGORY_NOT_FOUND)
        category.delete_detaching_tasks()
        return {'message': 'Categoria deletada'}, 200
