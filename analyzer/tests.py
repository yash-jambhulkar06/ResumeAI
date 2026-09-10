from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .views import extract_resume_text


class ResumeUploadTests(TestCase):
	def test_extracts_utf8_text_file(self):
		resume = SimpleUploadedFile(
			"resume.txt",
			"Python developer\nDjango experience".encode("utf-8"),
		)

		self.assertEqual(
			extract_resume_text(resume),
			"Python developer\nDjango experience",
		)

	def test_rejects_unsupported_file_type(self):
		resume = SimpleUploadedFile("resume.exe", b"not a resume")

		with self.assertRaisesMessage(ValueError, "Unsupported file type"):
			extract_resume_text(resume)

	def test_rejects_empty_file(self):
		resume = SimpleUploadedFile("resume.txt", b"")

		with self.assertRaisesMessage(ValueError, "file is empty"):
			extract_resume_text(resume)

	def test_rejects_files_over_five_mb(self):
		resume = SimpleUploadedFile("resume.txt", b"x" * (5 * 1024 * 1024 + 1))

		with self.assertRaisesMessage(ValueError, "too large"):
			extract_resume_text(resume)
