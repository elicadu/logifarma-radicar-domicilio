from django.test import TestCase
from django.utils.datastructures import MultiValueDict

from core import settings
from core.apps.base.forms import DigitaCelular
from core.apps.base.models import Municipio, Barrio
from core.apps.base.tests.test_fotoFormulaMedica import upload_foto
from core.apps.base.tests.test_wizards import TestWizard, get_request
from core.apps.base.views import FORMS


class DigitaCelularWizardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.mun = Municipio.objects.create(name='barranquilla', departamento='atlantico')
        cls.barr = Barrio.objects.create(name='el recreo', municipio=cls.mun,
                                         zona='norte', cod_zona=109,
                                         status=1)

    def setUp(self):
        self.testform = TestWizard.as_view(FORMS)
        self.request = get_request({'test_wizard-current_step': 'home'})
        self.response, self.instance = self.testform(self.request)
        self.request.POST = {'test_wizard-current_step': 'instrucciones'}
        self.response, self.instance = self.testform(self.request)
        self.request.POST = {'test_wizard-current_step': 'autorizacionServicio',
                             'autorizacionServicio-num_autorizacion': 99_999_999}
        self.response, self.instance = self.testform(self.request)
        image = upload_foto()
        self.request.POST = {'test_wizard-current_step': 'fotoFormulaMedica'}
        self.request.FILES = MultiValueDict({'fotoFormulaMedica-src': [image['src']]})
        self.response, self.instance = self.testform(self.request)
        self.request.POST = {'test_wizard-current_step': 'avisoDireccion'}
        self.response, self.instance = self.testform(self.request)
        self.request.POST = {'test_wizard-current_step': 'eligeMunicipio',
                             'eligeMunicipio-municipio': '1'}
        self.response, self.instance = self.testform(self.request)
        self.request.POST = {'test_wizard-current_step': 'digitaDireccionBarrio',
                             'digitaDireccionBarrio-direccion': 'AV MURILLO, 123456',
                             'digitaDireccionBarrio-barrio': str(DigitaCelularWizardTests.barr.id)}
        self.response, self.instance = self.testform(self.request)

    @classmethod
    def tearDownClass(cls):
        for file in settings.MEDIA_ROOT.iterdir():
            file.unlink()

    def test_step_name_is_digitaCelular(self):
        self.assertEqual(self.instance.steps.current, 'digitaCelular')

    def test_template_name_is_elige_municipio_html(self):
        self.assertEqual(self.instance.get_template_names()[0], 'digita_celular.html')

    def test_nextstep_is_digitaCorreo(self):
        self.assertEqual(self.instance.get_next_step(), 'digitaCorreo')

    def test_going_to_next_step(self):
        self.request.POST = {'test_wizard-current_step': 'digitaCelular',
                             'digitaCelular-celular': 321_456_9874}
        response, instance = self.testform(self.request)

        #  Al ser realizado el POST, deberá entrar en la siguiente vista
        self.assertEqual(self.instance.steps.current, 'digitaCorreo', 'No se pudo avanzar al siguiente paso')
        self.assertIn('digitaCelular', instance.storage.data['step_data'])


class DigitaCelularFormTests(TestCase):
    def test_invalid_numbers(self):
        for number in [-123456, 1, 0, 310_123_456, 414_123_4567]:
            with self.subTest(i=number):
                form = DigitaCelular(data={'celular': number})
                self.assertFalse(form.is_valid())
                self.assertEqual(form.errors['celular'],
                                 [f"Número de celular incorrecto:\n{number}"])

    def test_valid_number(self):
        for number in [300_000_0000, 301_601_2996, 311_111_1111]:
            with self.subTest(i=number):
                form = DigitaCelular(data={'celular': number})
                self.assertTrue(form.is_valid())
