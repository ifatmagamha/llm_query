import unittest
from src.validation.policy import PolicyValidator, SafetyException
from src.ir.models import QueryIR
from src.connectors.rdf import RdfConnector

class TestSystemUnit(unittest.TestCase):

    def test_policy_unsafe_raw(self):
        validator = PolicyValidator(allow_writes=False)
        
        # Test Mongo injection
        with self.assertRaises(SafetyException):
            validator.check_raw_safety('db.users.drop()', 'mongo')
            
        # Test Redis injection
        with self.assertRaises(SafetyException):
            validator.check_raw_safety('FLUSHALL', 'redis')
            
        # Safe query should pass
        self.assertTrue(validator.check_raw_safety('db.users.find()', 'mongo'))

    def test_policy_unsafe_ir(self):
        validator = PolicyValidator(allow_writes=False)
        with self.assertRaises(SafetyException):
            validator.check_ir_safety("MUTATION")
            
        self.assertTrue(validator.check_ir_safety("FIND"))

    def test_ir_model_validation(self):
        # Valid IR
        ir = QueryIR(intent="FIND", target_collection="movies")
        self.assertEqual(ir.intent, "FIND")
        
        # Invalid IR (missing required field)
        try:
            QueryIR(intent="FIND") # Missing target
            self.fail("Should have raised validation error")
        except Exception:
            pass

    def test_rdf_connector_memory(self):
        # Test the In-Memory RDF connector basic functionality
        conn = RdfConnector("memory")
        conn.connect()
        
        # Check metadata
        meta = conn.get_metadata()
        self.assertEqual(meta.db_type, "rdf_sparql")
        
        # Check execution
        res = conn.execute("SELECT ?s WHERE { ?s ?p ?o } LIMIT 1")
        self.assertEqual(res.status, "success")
        self.assertTrue(len(res.payload) > 0)

if __name__ == '__main__':
    unittest.main()
