from app import admin, db
from app.models import Category, Product, User, Receipt, ReceiptDetail
from flask_admin.contrib.sqla import ModelView


admin.add_view(ModelView(Category, db.session))
admin.add_view(ModelView(Product, db.session))
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(ReceiptDetail, db.session))