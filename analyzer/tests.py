from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .models import ResumeAnalysis
from .services.extractor import extract_resume_text
from .services.ats_auditor import run_ats_audit


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


class ATSAuditorTests(TestCase):
	def test_ats_audit_detects_contact_and_links(self):
		sample_resume = (
			"Jane Doe\n"
			"jane@example.com | (555) 123-4567\n"
			"linkedin.com/in/janedoe | github.com/janedoe\n"
			"Experience\n"
			"Senior Software Engineer\n"
			"- Increased API throughput by 45% serving 100k daily requests.\n"
			"- Led a team of 8 engineers and saved $120k annually.\n"
			"Education\n"
			"B.S. in Computer Science\n"
			"Skills\n"
			"Python, Django, PostgreSQL, Docker, AWS\n"
			"Projects\n"
			"Open source contributions and cloud architecture."
		)
		checks = run_ats_audit(sample_resume)
		labels = {c["label"]: c for c in checks}

		self.assertIn("Contact Information", labels)
		self.assertEqual(labels["Contact Information"]["status"], "pass")

		self.assertIn("Professional Links", labels)
		self.assertEqual(labels["Professional Links"]["status"], "pass")

		self.assertIn("Standard Section Headers", labels)
		self.assertEqual(labels["Standard Section Headers"]["status"], "pass")


class HomeViewTests(TestCase):
	def test_get_home_page_does_not_contain_job_role_input(self):
		response = self.client.get("/", secure=True)
		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, 'id="job_role"')
		self.assertNotContains(response, 'name="job_role"')

	def test_post_without_resume_shows_resume_error(self):
		response = self.client.post("/", {}, secure=True)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Please upload a readable resume or paste your resume text.")
		self.assertNotContains(response, "Please enter your target job role.")

	@patch("analyzer.views.analyze_resume_with_ai")
	def test_post_successful_resume_analysis(self, mock_ai):
		mock_ai.return_value = {
			"detected_role": "Backend Engineer",
			"seniority_level": "Senior",
			"overall_score": 85,
			"ats_score": 90,
			"category_scores": {
				"impact_metrics": 88,
				"ats_parsability": 92,
				"skills_depth": 85,
				"structure_brevity": 80,
			},
			"strengths": ["Strong quantifiable metrics"],
			"weaknesses": ["Add more cloud tools"],
			"missing_skills": ["Kubernetes"],
			"suggestions": ["Include architecture diagram link"],
			"bullet_rewrites": [
				{
					"original": "Built backends",
					"improved": "Built backend APIs reducing latency by 35% with Django",
					"reason": "Quantifies performance gain",
				}
			],
		}

		user = User.objects.create_user(username="testuser", password="password123")

		response = self.client.post(
			"/",
			{"resume_text": "Jane Doe jane@example.com (555) 123-4567 Experience Education Skills Projects"},
			secure=True,
		)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Backend Engineer")
		self.assertContains(response, "Senior")
		self.assertContains(response, "85")

		# Check DB record
		record = ResumeAnalysis.objects.filter(user=user).first()
		self.assertIsNotNone(record)
		self.assertEqual(record.job_role, "Backend Engineer")
		self.assertEqual(record.seniority_level, "Senior")
		self.assertEqual(record.overall_score, 85)
		self.assertIn("category_scores", record.details)


class HealthCheckTests(TestCase):
	def test_health_check_endpoint_returns_healthy(self):
		response = self.client.get("/health/", secure=True)
		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertEqual(data.get("status"), "healthy")
		self.assertEqual(data.get("database"), "connected")

