"""
Menu Cache Service - Serviço especializado para cache de menus
Otimizado para performance do sistema de menus dinâmicos
"""

import time
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import json
import hashlib
from app.infrastructure.cache.simplified_redis import SimplifiedRedisClient, get_simplified_redis
from app.domain.entities.menu import MenuEntity
from app.infrastructure.logging import logger


class MenuCacheService:
    """
    Serviço de cache especializado para menus dinâmicos
    
    Implementa estratégias de cache inteligentes para maximizar
    a performance do sistema de menus com invalidação automática.
    """
    
    def __init__(self, redis_client: Optional[SimplifiedRedisClient] = None):
        self.redis = redis_client
        
        # Configurações de TTL otimizadas
        self.ttl_config = {
            'menu_tree': 300,      # 5 minutos - árvore completa
            'menu_list': 600,      # 10 minutos - listagens 
            'menu_item': 1800,     # 30 minutos - item individual
            'user_menus': 300,     # 5 minutos - menus por usuário
            'search_results': 120, # 2 minutos - resultados de busca
            'statistics': 3600,    # 1 hora - estatísticas
        }
        
        # Prefixos de cache organizados
        self.prefixes = {
            'tree': 'menu_tree',
            'list': 'menu_list', 
            'item': 'menu_item',
            'user': 'user_menus',
            'search': 'menu_search',
            'stats': 'menu_stats',
            'hierarchy': 'menu_hierarchy'
        }
    
    async def _get_redis(self) -> SimplifiedRedisClient:
        """Obter cliente Redis (lazy loading)"""
        if not self.redis:
            self.redis = await get_simplified_redis()
        return self.redis
    
    def _make_cache_key(self, prefix: str, *args) -> str:
        """Criar chave de cache consistente"""
        parts = [str(arg) for arg in args if arg is not None]
        key_suffix = ':'.join(parts)
        
        # Gerar hash para chaves muito longas (>200 chars)
        if len(key_suffix) > 200:
            hash_suffix = hashlib.md5(key_suffix.encode()).hexdigest()[:12]
            key_suffix = f"{key_suffix[:180]}:{hash_suffix}"
        
        return f"{self.prefixes[prefix]}:{key_suffix}"
    
    def _serialize_menu_entity(self, entity: MenuEntity) -> Dict:
        """Serializar MenuEntity para cache"""
        return entity.to_dict()
    
    def _deserialize_menu_entity(self, data: Dict) -> MenuEntity:
        """Deserializar dados do cache para MenuEntity"""
        return MenuEntity.from_dict(data)
    
    def _serialize_menu_list(self, entities: List[MenuEntity]) -> List[Dict]:
        """Serializar lista de MenuEntity"""
        return [entity.to_dict() for entity in entities]
    
    def _deserialize_menu_list(self, data: List[Dict]) -> List[MenuEntity]:
        """Deserializar lista do cache"""
        return [MenuEntity.from_dict(item) for item in data]
    
    async def cache_menu_tree(self, 
                             tree: List[MenuEntity], 
                             user_id: Optional[int] = None,
                             context_type: str = "system",
                             context_id: Optional[int] = None) -> bool:
        """Cache da árvore hierárquica de menus"""
        redis = await self._get_redis()
        
        try:
            cache_key = self._make_cache_key('tree', user_id, context_type, context_id)
            serialized_tree = self._serialize_menu_list(tree)
            
            # Adicionar metadados de cache
            cache_data = {
                'tree': serialized_tree,
                'cached_at': datetime.now().isoformat(),
                'user_id': user_id,
                'context_type': context_type,
                'context_id': context_id,
                'total_menus': self._count_tree_nodes(tree)
            }
            
            success = await redis.set(cache_key, cache_data, self.ttl_config['menu_tree'])
            
            if success:
                logger.debug("Menu tree cached", 
                           key=cache_key, 
                           total_menus=cache_data['total_menus'],
                           user_id=user_id)
            
            return success
            
        except Exception as e:
            logger.error("Error caching menu tree", error=str(e), user_id=user_id)
            return False
    
    async def get_menu_tree(self,
                           user_id: Optional[int] = None,
                           context_type: str = "system", 
                           context_id: Optional[int] = None) -> Optional[List[MenuEntity]]:
        """Recuperar árvore de menus do cache"""
        redis = await self._get_redis()
        
        try:
            cache_key = self._make_cache_key('tree', user_id, context_type, context_id)
            cached_data = await redis.get(cache_key)
            
            if cached_data and isinstance(cached_data, dict):
                tree_data = cached_data.get('tree')
                if tree_data:
                    tree = self._deserialize_menu_list(tree_data)
                    
                    logger.debug("Menu tree cache hit", 
                               key=cache_key,
                               total_menus=cached_data.get('total_menus', 0),
                               user_id=user_id)
                    
                    return tree
            
            logger.debug("Menu tree cache miss", key=cache_key, user_id=user_id)
            return None
            
        except Exception as e:
            logger.error("Error retrieving menu tree from cache", error=str(e), user_id=user_id)
            return None
    
    async def cache_menu_list(self, 
                             menus: List[MenuEntity],
                             skip: int = 0,
                             limit: int = 100,
                             parent_id: Optional[int] = None,
                             status: Optional[str] = None,
                             search: Optional[str] = None,
                             level: Optional[int] = None) -> bool:
        """Cache de listagem de menus"""
        redis = await self._get_redis()
        
        try:
            cache_key = self._make_cache_key('list', skip, limit, parent_id, status, search, level)
            serialized_menus = self._serialize_menu_list(menus)
            
            cache_data = {
                'menus': serialized_menus,
                'cached_at': datetime.now().isoformat(),
                'filters': {
                    'skip': skip,
                    'limit': limit,
                    'parent_id': parent_id,
                    'status': status,
                    'search': search,
                    'level': level
                },
                'count': len(menus)
            }
            
            success = await redis.set(cache_key, cache_data, self.ttl_config['menu_list'])
            
            if success:
                logger.debug("Menu list cached", key=cache_key, count=len(menus))
            
            return success
            
        except Exception as e:
            logger.error("Error caching menu list", error=str(e))
            return False
    
    async def get_menu_list(self,
                           skip: int = 0,
                           limit: int = 100,
                           parent_id: Optional[int] = None,
                           status: Optional[str] = None,
                           search: Optional[str] = None,
                           level: Optional[int] = None) -> Optional[List[MenuEntity]]:
        """Recuperar listagem de menus do cache"""
        redis = await self._get_redis()
        
        try:
            cache_key = self._make_cache_key('list', skip, limit, parent_id, status, search, level)
            cached_data = await redis.get(cache_key)
            
            if cached_data and isinstance(cached_data, dict):
                menus_data = cached_data.get('menus')
                if menus_data:
                    menus = self._deserialize_menu_list(menus_data)
                    
                    logger.debug("Menu list cache hit", 
                               key=cache_key,
                               count=cached_data.get('count', 0))
                    
                    return menus
            
            logger.debug("Menu list cache miss", key=cache_key)
            return None
            
        except Exception as e:
            logger.error("Error retrieving menu list from cache", error=str(e))
            return None
    
    async def cache_menu_item(self, menu: MenuEntity) -> bool:
        """Cache de item de menu individual"""
        if not menu.id:
            return False
            
        redis = await self._get_redis()
        
        try:
            cache_key = self._make_cache_key('item', menu.id)
            serialized_menu = self._serialize_menu_entity(menu)
            
            success = await redis.set(cache_key, serialized_menu, self.ttl_config['menu_item'])
            
            if success:
                logger.debug("Menu item cached", key=cache_key, menu_id=menu.id, name=menu.name)
            
            return success
            
        except Exception as e:
            logger.error("Error caching menu item", error=str(e), menu_id=menu.id)
            return False
    
    async def get_menu_item(self, menu_id: int) -> Optional[MenuEntity]:
        """Recuperar item de menu do cache"""
        redis = await self._get_redis()
        
        try:
            cache_key = self._make_cache_key('item', menu_id)
            cached_data = await redis.get(cache_key)
            
            if cached_data:
                menu = self._deserialize_menu_entity(cached_data)
                logger.debug("Menu item cache hit", key=cache_key, menu_id=menu_id)
                return menu
            
            logger.debug("Menu item cache miss", key=cache_key, menu_id=menu_id)
            return None
            
        except Exception as e:
            logger.error("Error retrieving menu item from cache", error=str(e), menu_id=menu_id)
            return None
    
    async def cache_user_menus(self, 
                              menus: List[MenuEntity],
                              user_id: int,
                              context_type: str = "system",
                              context_id: Optional[int] = None) -> bool:
        """Cache de menus específicos do usuário"""
        redis = await self._get_redis()
        
        try:
            cache_key = self._make_cache_key('user', user_id, context_type, context_id)
            serialized_menus = self._serialize_menu_list(menus)
            
            cache_data = {
                'menus': serialized_menus,
                'cached_at': datetime.now().isoformat(),
                'user_id': user_id,
                'context_type': context_type,
                'context_id': context_id,
                'count': len(menus)
            }
            
            success = await redis.set(cache_key, cache_data, self.ttl_config['user_menus'])
            
            if success:
                logger.debug("User menus cached", 
                           key=cache_key, 
                           user_id=user_id,
                           count=len(menus))
            
            return success
            
        except Exception as e:
            logger.error("Error caching user menus", error=str(e), user_id=user_id)
            return False
    
    async def get_user_menus(self,
                            user_id: int,
                            context_type: str = "system",
                            context_id: Optional[int] = None) -> Optional[List[MenuEntity]]:
        """Recuperar menus do usuário do cache"""
        redis = await self._get_redis()
        
        try:
            cache_key = self._make_cache_key('user', user_id, context_type, context_id)
            cached_data = await redis.get(cache_key)
            
            if cached_data and isinstance(cached_data, dict):
                menus_data = cached_data.get('menus')
                if menus_data:
                    menus = self._deserialize_menu_list(menus_data)
                    
                    logger.debug("User menus cache hit", 
                               key=cache_key,
                               user_id=user_id,
                               count=cached_data.get('count', 0))
                    
                    return menus
            
            logger.debug("User menus cache miss", key=cache_key, user_id=user_id)
            return None
            
        except Exception as e:
            logger.error("Error retrieving user menus from cache", error=str(e), user_id=user_id)
            return None
    
    async def cache_search_results(self, 
                                  results: List[MenuEntity],
                                  query: str,
                                  user_id: Optional[int] = None,
                                  context_type: str = "system",
                                  limit: int = 50) -> bool:
        """Cache de resultados de busca"""
        redis = await self._get_redis()
        
        try:
            # Hash da query para chave consistente
            query_hash = hashlib.md5(query.lower().encode()).hexdigest()[:8]
            cache_key = self._make_cache_key('search', query_hash, user_id, context_type, limit)
            
            serialized_results = self._serialize_menu_list(results)
            
            cache_data = {
                'results': serialized_results,
                'query': query,
                'cached_at': datetime.now().isoformat(),
                'user_id': user_id,
                'context_type': context_type,
                'count': len(results)
            }
            
            success = await redis.set(cache_key, cache_data, self.ttl_config['search_results'])
            
            if success:
                logger.debug("Search results cached", 
                           key=cache_key,
                           query=query,
                           count=len(results))
            
            return success
            
        except Exception as e:
            logger.error("Error caching search results", error=str(e), query=query)
            return False
    
    async def get_search_results(self,
                                query: str,
                                user_id: Optional[int] = None,
                                context_type: str = "system",
                                limit: int = 50) -> Optional[List[MenuEntity]]:
        """Recuperar resultados de busca do cache"""
        redis = await self._get_redis()
        
        try:
            query_hash = hashlib.md5(query.lower().encode()).hexdigest()[:8]
            cache_key = self._make_cache_key('search', query_hash, user_id, context_type, limit)
            cached_data = await redis.get(cache_key)
            
            if cached_data and isinstance(cached_data, dict):
                # Verificar se a query é exatamente a mesma
                if cached_data.get('query') == query:
                    results_data = cached_data.get('results')
                    if results_data:
                        results = self._deserialize_menu_list(results_data)
                        
                        logger.debug("Search results cache hit",
                                   key=cache_key,
                                   query=query,
                                   count=cached_data.get('count', 0))
                        
                        return results
            
            logger.debug("Search results cache miss", key=cache_key, query=query)
            return None
            
        except Exception as e:
            logger.error("Error retrieving search results from cache", error=str(e), query=query)
            return None
    
    async def invalidate_menu_caches(self, menu_id: Optional[int] = None) -> int:
        """Invalidar caches relacionados a menus"""
        redis = await self._get_redis()
        
        try:
            patterns_to_clear = []
            
            if menu_id:
                # Invalidar cache específico do menu
                patterns_to_clear.extend([
                    f"{self.prefixes['item']}:{menu_id}:*",
                    f"{self.prefixes['item']}:{menu_id}"
                ])
            
            # Invalidar caches gerais (sempre)
            patterns_to_clear.extend([
                f"{self.prefixes['tree']}:*",
                f"{self.prefixes['list']}:*",
                f"{self.prefixes['user']}:*",
                f"{self.prefixes['search']}:*",
                f"{self.prefixes['hierarchy']}:*"
            ])
            
            total_deleted = 0
            for pattern in patterns_to_clear:
                deleted = await redis.clear_pattern(pattern)
                total_deleted += deleted
            
            logger.info("Menu caches invalidated", 
                       menu_id=menu_id,
                       patterns=len(patterns_to_clear),
                       total_deleted=total_deleted)
            
            return total_deleted
            
        except Exception as e:
            logger.error("Error invalidating menu caches", error=str(e), menu_id=menu_id)
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do cache de menus"""
        redis = await self._get_redis()
        
        try:
            redis_info = await redis.get_info()
            
            # Estatísticas específicas do cache de menus
            stats = {
                'redis_connected': redis_info.get('connected', False),
                'redis_info': redis_info,
                'cache_prefixes': list(self.prefixes.keys()),
                'ttl_config': self.ttl_config,
                'timestamp': datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error("Error getting cache stats", error=str(e))
            return {
                'error': str(e),
                'redis_connected': False,
                'timestamp': datetime.now().isoformat()
            }
    
    def _count_tree_nodes(self, tree: List[MenuEntity]) -> int:
        """Contar total de nós na árvore recursivamente"""
        count = len(tree)
        for node in tree:
            count += self._count_tree_nodes(node.children)
        return count
    
    async def warm_cache(self, 
                        menu_tree: List[MenuEntity],
                        user_id: Optional[int] = None,
                        context_type: str = "system") -> Dict[str, bool]:
        """Pré-aquecer cache com dados principais"""
        results = {}
        
        # Cache da árvore principal
        results['tree'] = await self.cache_menu_tree(menu_tree, user_id, context_type)
        
        # Cache de itens individuais
        all_menus = self._flatten_tree(menu_tree)
        item_results = []
        for menu in all_menus:
            success = await self.cache_menu_item(menu)
            item_results.append(success)
        
        results['items'] = all(item_results) if item_results else True
        results['items_count'] = len(item_results)
        
        logger.info("Cache warming completed", 
                   results=results,
                   total_menus=len(all_menus))
        
        return results
    
    def _flatten_tree(self, tree: List[MenuEntity]) -> List[MenuEntity]:
        """Achatar árvore em lista plana"""
        flat_list = []
        for node in tree:
            flat_list.append(node)
            flat_list.extend(self._flatten_tree(node.children))
        return flat_list


# Instância global do serviço
_menu_cache_service = None

async def get_menu_cache_service() -> MenuCacheService:
    """Obter instância global do serviço de cache de menus"""
    global _menu_cache_service
    if _menu_cache_service is None:
        redis_client = await get_simplified_redis()
        _menu_cache_service = MenuCacheService(redis_client)
    return _menu_cache_service