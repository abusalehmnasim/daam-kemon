export interface ProductOut {
  id: number;
  name: string;
  brand: string | null;
  category: string;
  subcategory: string | null;
  size_value: number | null;
  size_unit: string | null;
  is_loose: boolean;
}

export interface StoreOfferingOut {
  store_product_id: number;
  store_name: string;
  store_display_name: string;
  name: string;
  price: number;
  original_price: number | null;
  in_stock: boolean;
  url: string | null;
  image_url: string | null;
  delivery_fee: number | null;
  match_confidence: number | null;
  match_method: string | null;
  is_sponsored: boolean;
}

export interface ProductGroupOut {
  product: ProductOut;
  offerings: StoreOfferingOut[];
  cheapest_price: number | null;
  cheapest_store: string | null;
  alternatives: ProductGroupOut[];
}

export interface AggregatedOffering {
  store_product_id: number;
  product_id: number | null;
  store_name: string;
  store_display_name: string;
  brand: string | null;
  product_name: string;
  store_product_name: string;
  price: number;
  original_price: number | null;
  in_stock: boolean;
  url: string | null;
  image_url: string | null;
  match_confidence: number | null;
  match_method: string | null;
  is_sponsored: boolean;
}

export interface AggregatedGroup {
  category: string;
  subcategory: string | null;
  display_name: string;
  size_value: number | null;
  size_unit: string | null;
  is_loose: boolean;
  offerings: AggregatedOffering[];
  cheapest_price: number | null;
  cheapest_brand: string | null;
  cheapest_store: string | null;
}

export interface SearchResponse {
  query: string;
  parsed_category: string | null;
  parsed_size: string | null;
  groups: AggregatedGroup[];
  total_groups: number;
}

export interface SubcategoryOut {
  key: string;
  display: string;
}

export interface CategoryOut {
  key: string;
  display: string;
  product_count: number;
  listing_count: number;
  subcategories: SubcategoryOut[];
}

export interface CategoryGroupOut {
  group: string;
  categories: CategoryOut[];
}

export interface BasketItemIn {
  product_id?: number;
  query?: string;
  quantity: number;
}

export interface StoreLineItemOut {
  item_key: string;
  label: string;
  store_product_id: number;
  store_product_name: string;
  unit_price: number;
  quantity: number;
  line_total: number;
}

export interface StorePlanOut {
  store: string;
  store_display_name: string;
  items: StoreLineItemOut[];
  items_subtotal: number;
  delivery_fee: number;
  total: number;
  missing_items: string[];
}

export interface BasketOptimizeResponse {
  single_store: StorePlanOut | null;
  split: StorePlanOut[];
  split_savings: number;
  all_single_store: StorePlanOut[];
  unresolved_items: string[];
}
