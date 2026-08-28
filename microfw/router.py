import re

class TrieNode:
    def __init__(self):
        self.children = {}
        self.handler_info = None
        self.param_name = None
        self.is_param = False

class RadixRouter:
    def __init__(self):
        # We need a Trie per HTTP method
        self.roots = {}
        
    def _get_root(self, method: str) -> TrieNode:
        method = method.upper()
        if method not in self.roots:
            self.roots[method] = TrieNode()
        return self.roots[method]

    def add_route(self, method: str, path: str, handler_info: dict):
        root = self._get_root(method)
        node = root
        
        # Split path into parts, e.g., "/users/{id}/profile" -> ["", "users", "{id}", "profile"]
        parts = path.split("/")
        
        for part in parts:
            if not part and node == root:
                # Handle root path specifically if needed, but split("/") handles it
                # For "/", parts = ["", ""]
                pass

            is_param = False
            param_name = None
            
            # Detect parameter like {user_id}
            if part.startswith("{") and part.endswith("}"):
                is_param = True
                param_name = part[1:-1]
                # In our Trie, we use a special key for params to traverse
                part_key = "*" 
            else:
                part_key = part

            if part_key not in node.children:
                new_node = TrieNode()
                if is_param:
                    new_node.is_param = True
                    new_node.param_name = param_name
                node.children[part_key] = new_node
                
            node = node.children[part_key]
            
        node.handler_info = handler_info

    def match_route(self, method: str, path: str):
        """
        Returns (handler_info, kwargs) or (None, {})
        """
        method = method.upper()
        if method not in self.roots:
            return None, {}
            
        node = self.roots[method]
        parts = path.split("/")
        kwargs = {}
        
        for part in parts:
            if part in node.children:
                node = node.children[part]
            elif "*" in node.children:
                # It's a parameter node
                node = node.children["*"]
                kwargs[node.param_name] = part
            else:
                return None, {}
                
        if node.handler_info:
            return node.handler_info, kwargs
            
        return None, {}
