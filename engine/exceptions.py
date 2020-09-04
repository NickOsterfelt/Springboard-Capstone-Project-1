class InvalidFormInput(Exception):
    """Exception raised when form input is not correct.

    Attributes:
        input_name -- input that triggered the exception
        value -- value that is invalid
        message -- message describing why it was invalid
    """

    def __init__(self, input_name, value, message):
        self.input_name = input_name
        self.value = value
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.input_name} : {self.value}, {self.message}'
