import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..base_connector import BasePlatformConnector, AuthType, PlatformCapability, ApiResponse

class ShopifyConnector(BasePlatformConnector):
    """Shopify integration for e-commerce automation"""
    
    def __init__(self, credentials: Dict[str, str], config: Optional[Dict[str, Any]] = None):
        super().__init__(credentials, config)
        self.shop_domain = credentials.get("shop_domain", "")
        if not self.shop_domain.endswith(".myshopify.com"):
            self.shop_domain = f"{self.shop_domain}.myshopify.com"
    
    @property
    def platform_name(self) -> str:
        return "shopify"
    
    @property
    def auth_type(self) -> AuthType:
        return AuthType.BEARER_TOKEN
    
    @property
    def base_url(self) -> str:
        return f"https://{self.shop_domain}/admin/api/2023-04"
    
    async def authenticate(self) -> bool:
        """Authenticate with Shopify API"""
        try:
            if not self.validate_credentials(["access_token", "shop_domain"]):
                return False
            
            self.auth_token = self.credentials["access_token"]
            
            # Test authentication by getting shop info
            response = await self.make_request("GET", "/shop.json")
            
            if response.success:
                self.logger.info("Shopify authentication successful")
                return True
            else:
                self.logger.error(f"Shopify authentication failed: {response.error}")
                return False
                
        except Exception as e:
            self.logger.error(f"Shopify authentication error: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Shopify API connection"""
        try:
            start_time = datetime.now()
            response = await self.make_request("GET", "/shop.json")
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": response.success,
                "platform": "shopify",
                "shop_domain": self.shop_domain,
                "response_time": response_time,
                "error": response.error if not response.success else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "platform": "shopify",
                "error": str(e)
            }
    
    async def get_capabilities(self) -> List[PlatformCapability]:
        """Get Shopify integration capabilities"""
        return [
            PlatformCapability(
                name="Product Management",
                description="Create, read, update and manage products",
                methods=["get_products", "get_product", "create_product", "update_product", "delete_product"],
                rate_limit=40
            ),
            PlatformCapability(
                name="Order Management",
                description="Manage customer orders and fulfillment",
                methods=["get_orders", "get_order", "update_order", "fulfill_order", "cancel_order"],
                rate_limit=40
            ),
            PlatformCapability(
                name="Customer Management",
                description="Manage customer data and relationships",
                methods=["get_customers", "get_customer", "create_customer", "update_customer"],
                rate_limit=40
            ),
            PlatformCapability(
                name="Inventory Management", 
                description="Track and manage inventory levels",
                methods=["get_inventory", "update_inventory", "track_inventory"],
                rate_limit=40
            ),
            PlatformCapability(
                name="Analytics & Reports",
                description="Access sales analytics and generate reports",
                methods=["get_analytics", "generate_report", "get_sales_data"],
                rate_limit=20
            )
        ]
    
    # Shop Information
    async def get_shop_info(self) -> ApiResponse:
        """Get shop information"""
        return await self.make_request("GET", "/shop.json")
    
    # Product Methods
    async def get_products(self, limit: int = 50, page_info: Optional[str] = None,
                          status: Optional[str] = None) -> ApiResponse:
        """Get products from Shopify store"""
        params = {"limit": str(limit)}
        
        if page_info:
            params["page_info"] = page_info
        
        if status:
            params["status"] = status
        
        return await self.make_request("GET", "/products.json", params=params)
    
    async def get_product(self, product_id: str) -> ApiResponse:
        """Get specific product by ID"""
        return await self.make_request("GET", f"/products/{product_id}.json")
    
    async def create_product(self, product_data: Dict[str, Any]) -> ApiResponse:
        """Create a new product"""
        return await self.make_request("POST", "/products.json", data={"product": product_data})
    
    async def update_product(self, product_id: str, product_data: Dict[str, Any]) -> ApiResponse:
        """Update existing product"""
        return await self.make_request("PUT", f"/products/{product_id}.json", 
                                     data={"product": product_data})
    
    async def delete_product(self, product_id: str) -> ApiResponse:
        """Delete a product"""
        return await self.make_request("DELETE", f"/products/{product_id}.json")
    
    async def get_product_variants(self, product_id: str) -> ApiResponse:
        """Get variants for a product"""
        return await self.make_request("GET", f"/products/{product_id}/variants.json")
    
    async def create_product_variant(self, product_id: str, variant_data: Dict[str, Any]) -> ApiResponse:
        """Create a product variant"""
        return await self.make_request("POST", f"/products/{product_id}/variants.json",
                                     data={"variant": variant_data})
    
    # Order Methods  
    async def get_orders(self, limit: int = 50, status: str = "any",
                        created_at_min: Optional[str] = None) -> ApiResponse:
        """Get orders from store"""
        params = {
            "limit": str(limit),
            "status": status
        }
        
        if created_at_min:
            params["created_at_min"] = created_at_min
        
        return await self.make_request("GET", "/orders.json", params=params)
    
    async def get_order(self, order_id: str) -> ApiResponse:
        """Get specific order by ID"""
        return await self.make_request("GET", f"/orders/{order_id}.json")
    
    async def update_order(self, order_id: str, order_data: Dict[str, Any]) -> ApiResponse:
        """Update an existing order"""
        return await self.make_request("PUT", f"/orders/{order_id}.json",
                                     data={"order": order_data})
    
    async def cancel_order(self, order_id: str, reason: Optional[str] = None) -> ApiResponse:
        """Cancel an order"""
        cancel_data = {}
        if reason:
            cancel_data["reason"] = reason
        
        return await self.make_request("POST", f"/orders/{order_id}/cancel.json", data=cancel_data)
    
    async def fulfill_order(self, order_id: str, fulfillment_data: Dict[str, Any]) -> ApiResponse:
        """Create fulfillment for an order"""
        return await self.make_request("POST", f"/orders/{order_id}/fulfillments.json",
                                     data={"fulfillment": fulfillment_data})
    
    # Customer Methods
    async def get_customers(self, limit: int = 50, page_info: Optional[str] = None) -> ApiResponse:
        """Get customers"""
        params = {"limit": str(limit)}
        
        if page_info:
            params["page_info"] = page_info
        
        return await self.make_request("GET", "/customers.json", params=params)
    
    async def get_customer(self, customer_id: str) -> ApiResponse:
        """Get specific customer by ID"""
        return await self.make_request("GET", f"/customers/{customer_id}.json")
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> ApiResponse:
        """Create a new customer"""
        return await self.make_request("POST", "/customers.json", data={"customer": customer_data})
    
    async def update_customer(self, customer_id: str, customer_data: Dict[str, Any]) -> ApiResponse:
        """Update existing customer"""
        return await self.make_request("PUT", f"/customers/{customer_id}.json",
                                     data={"customer": customer_data})
    
    async def search_customers(self, query: str) -> ApiResponse:
        """Search customers"""
        params = {"query": query}
        return await self.make_request("GET", "/customers/search.json", params=params)
    
    # Inventory Methods
    async def get_inventory_levels(self, location_id: Optional[str] = None) -> ApiResponse:
        """Get inventory levels"""
        params = {}
        if location_id:
            params["location_ids"] = location_id
        
        return await self.make_request("GET", "/inventory_levels.json", params=params)
    
    async def adjust_inventory(self, inventory_item_id: str, location_id: str,
                             quantity_adjustment: int) -> ApiResponse:
        """Adjust inventory quantity"""
        adjustment_data = {
            "inventory_item_id": inventory_item_id,
            "location_id": location_id,
            "quantity_adjustment": quantity_adjustment
        }
        
        return await self.make_request("POST", "/inventory_levels/adjust.json", data=adjustment_data)
    
    # Collections Methods
    async def get_collections(self) -> ApiResponse:
        """Get product collections"""
        return await self.make_request("GET", "/custom_collections.json")
    
    async def create_collection(self, collection_data: Dict[str, Any]) -> ApiResponse:
        """Create a new collection"""
        return await self.make_request("POST", "/custom_collections.json",
                                     data={"custom_collection": collection_data})
    
    # Analytics Methods
    async def get_shop_analytics(self) -> ApiResponse:
        """Get basic shop analytics"""
        # Get recent orders count
        orders_response = await self.get_orders(limit=250)
        
        if orders_response.success:
            orders = orders_response.data.get("orders", [])
            
            total_sales = sum(float(order.get("total_price", 0)) for order in orders)
            order_count = len(orders)
            
            # Get product count
            products_response = await self.get_products(limit=250)
            product_count = len(products_response.data.get("products", [])) if products_response.success else 0
            
            # Get customer count
            customers_response = await self.get_customers(limit=250)
            customer_count = len(customers_response.data.get("customers", [])) if customers_response.success else 0
            
            analytics = {
                "total_sales": total_sales,
                "order_count": order_count,
                "product_count": product_count,
                "customer_count": customer_count,
                "average_order_value": total_sales / order_count if order_count > 0 else 0
            }
            
            return ApiResponse(success=True, data=analytics)
        
        return ApiResponse(success=False, error="Failed to fetch analytics data")
    
    # Automation Methods
    async def bulk_update_products(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk update multiple products"""
        results = []
        
        for update in updates:
            product_id = update.get("product_id")
            product_data = update.get("data")
            
            if product_id and product_data:
                response = await self.update_product(product_id, product_data)
                results.append({
                    "product_id": product_id,
                    "success": response.success,
                    "error": response.error
                })
                
                # Rate limiting
                await asyncio.sleep(0.5)
        
        successful_updates = len([r for r in results if r["success"]])
        
        return {
            "total_updates": len(updates),
            "successful_updates": successful_updates,
            "failed_updates": len(updates) - successful_updates,
            "results": results
        }
    
    async def auto_fulfill_orders(self, tracking_company: str = "Other") -> Dict[str, Any]:
        """Automatically fulfill paid orders"""
        # Get unfulfilled orders
        orders_response = await self.get_orders(limit=50, status="open")
        
        if not orders_response.success:
            return {"error": "Failed to fetch orders", "success": False}
        
        orders = orders_response.data.get("orders", [])
        fulfilled_orders = []
        
        for order in orders:
            order_id = order.get("id")
            financial_status = order.get("financial_status")
            fulfillment_status = order.get("fulfillment_status")
            
            # Only fulfill paid and unfulfilled orders
            if financial_status == "paid" and fulfillment_status is None:
                line_items = order.get("line_items", [])
                
                fulfillment_data = {
                    "tracking_company": tracking_company,
                    "notify_customer": True,
                    "line_items": [
                        {
                            "id": item["id"],
                            "quantity": item["quantity"]
                        }
                        for item in line_items
                    ]
                }
                
                fulfill_response = await self.fulfill_order(order_id, fulfillment_data)
                
                if fulfill_response.success:
                    fulfilled_orders.append(order_id)
                
                # Rate limiting
                await asyncio.sleep(1)
        
        return {
            "success": True,
            "fulfilled_orders": len(fulfilled_orders),
            "order_ids": fulfilled_orders
        }
    
    async def inventory_alert_check(self, threshold: int = 5) -> Dict[str, Any]:
        """Check for low inventory items"""
        # Get inventory levels
        inventory_response = await self.get_inventory_levels()
        
        if not inventory_response.success:
            return {"error": "Failed to fetch inventory", "success": False}
        
        inventory_levels = inventory_response.data.get("inventory_levels", [])
        low_stock_items = []
        
        for item in inventory_levels:
            available = item.get("available", 0)
            if available is not None and available <= threshold:
                # Get product info
                inventory_item_id = item.get("inventory_item_id")
                
                low_stock_items.append({
                    "inventory_item_id": inventory_item_id,
                    "available_quantity": available,
                    "location_id": item.get("location_id")
                })
        
        return {
            "success": True,
            "low_stock_count": len(low_stock_items),
            "threshold": threshold,
            "low_stock_items": low_stock_items
        }