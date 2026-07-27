"""
Mock Neo4j module for Cloud Shell compatibility.
"""

class GraphDatabase:
    @staticmethod
    def driver(uri, auth=None):
        return MockDriver()

class MockDriver:
    def __init__(self):
        self.session = MockSession
    
    def session(self):
        return MockSession()
    
    def close(self):
        pass
    
    def verify_connectivity(self):
        return True

class MockSession:
    def __init__(self):
        self._run = MockRun()
    
    def run(self, query, **parameters):
        return MockResult()
    
    def close(self):
        pass

class MockRun:
    def data(self):
        return []

class MockResult:
    def __init__(self):
        self._data = []
    
    def data(self):
        return []
    
    def single(self):
        return None
    
    def __iter__(self):
        return iter([])
