import unittest

class Test_TestUser(unittest.TestCase):

    def test_user_has_correct_attributes(self):
        """
        Check if all attributes heve the desired type
        """

        from src.settings.info import User, Path
        USER = User()
        types = [
            type(USER.email) == str,
            type(USER.language) == str,
            type(USER.language_audio) == str,
            type(USER.language_text) == str,
            type(USER.paths) == dict
        ]
        result = all(types)
        self.assertTrue(result, "1 or more attributes are identified with the wrong type")

if __name__ == '__main__':
    unittest.main()
