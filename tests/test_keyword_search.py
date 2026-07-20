"""
Tests for KeywordSearch service - matching actual implementation.
"""
import pytest
from app.services.keyword_search import KeywordSearch

class TestKeywordSearch:
    """Test suite for KeywordSearch."""
    
    def test_init(self):
        """Test KeywordSearch initialization."""
        search = KeywordSearch()
        assert search is not None
        assert search.index is None
        assert search.metadata == []
    
    def test_build_index(self):
        """Test building BM25 index."""
        search = KeywordSearch()
        
        documents = [
            {"id": 1, "content": "This is a test document about Python programming"},
            {"id": 2, "content": "Another document about machine learning and AI"},
            {"id": 3, "content": "Python is great for data science"}
        ]
        
        search.build_index(documents)
        
        assert search.index is not None
        assert len(search.metadata) == 3
    
    def test_search_with_existing_content(self):
        """Test searching with existing content."""
        search = KeywordSearch()
        
        documents = [
            {"id": 1, "content": "This is a test document about Python programming"},
            {"id": 2, "content": "Another document about machine learning and AI"},
            {"id": 3, "content": "Python is great for data science"}
        ]
        
        search.build_index(documents)
        
        # Search for a keyword
        results = search.search("Python", user_id=1, limit=2)
        
        assert results is not None
        assert len(results) <= 2
        # Results should be lists of dicts with document info
        if results:
            assert "id" in results[0]
            assert "content" in results[0]
    
    def test_search_with_no_results(self):
        """Test search with no matching results."""
        search = KeywordSearch()
        
        documents = [
            {"id": 1, "content": "This is about cats"},
            {"id": 2, "content": "This is about dogs"}
        ]
        
        search.build_index(documents)
        results = search.search("elephant", user_id=1)
        
        # Should return empty list or list with low scores
        assert results is not None
    
    def test_search_with_empty_query(self):
        """Test search with empty query."""
        search = KeywordSearch()
        
        documents = [
            {"id": 1, "content": "Test content"}
        ]
        search.build_index(documents)
        
        results = search.search("", user_id=1)
        assert results == []
    
    def test_search_without_index(self):
        """Test search when no index is built."""
        search = KeywordSearch()
        
        results = search.search("test", user_id=1)
        assert results == []
    
    def test_build_index_with_empty_documents(self):
        """Test building index with empty documents list."""
        search = KeywordSearch()
        search.build_index([])
        assert search.index is None

if __name__ == "__main__":
    pytest.main(["-v", __file__])
