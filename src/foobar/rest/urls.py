from rest_framework import routers

from .views.wallet import WalletAPI, WalletTrxAPI
from .views.product import ProductAPI, ProductCategoryAPI
from .views.account import AccountAPI
from .views.purchase import PurchaseAPI

router = routers.SimpleRouter()
router.register(r'wallets', WalletAPI, 'wallets')
router.register(r'wallet_trxs', WalletTrxAPI, 'wallet_trxs')
router.register(r'products', ProductAPI, 'products')
router.register(r'categories', ProductCategoryAPI, 'categories')
router.register(r'accounts', AccountAPI, 'accounts')
router.register(r'purchases', PurchaseAPI, 'purchases')

urlpatterns = tuple(router.urls)
