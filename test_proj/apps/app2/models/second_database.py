from datavalidation import data_validator, PASS, FAIL, NA

from app1.models.base import BaseModel


class SecondDatabase(BaseModel):

    @data_validator
    def test_foobar(self):
        """ tests: returning PASS/FAIL/NA """
        if self.foobar is None:
            return NA
        elif self.foobar < 10:
            return PASS
        return FAIL("foobar too large!")
