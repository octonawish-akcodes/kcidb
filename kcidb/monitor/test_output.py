"""kcdib.monitor.output module tests"""

import email
import unittest
from kcidb.io import schema
from kcidb import orm, db, oo
from kcidb.monitor.output import NotificationMessage, Notification

# Disable long line checking for JSON data
# flake8: noqa
# pylint: disable=line-too-long


class NotificationTestCase(unittest.TestCase):
    """kcidb.monitor.output.Notification test case"""

    def setUp(self):
        """Setup tests"""
        # pylint: disable=invalid-name
        self.maxDiff = None
        self.version = dict(
            major=schema.LATEST.major,
            minor=schema.LATEST.minor
        )

    def test_min(self):
        """Check minimal Notification functionality"""

        db_client = db.Client("sqlite::memory:")
        db_client.init()
        oo_client = oo.Client(db_client)
        db_client.load({
            "version": self.version,
            "checkouts": [
                {
                    "contacts": [
                        "rdma-dev-team@redhat.com"
                    ],
                    "start_time": "2020-03-02T15:16:15.790000+00:00",
                    "git_repository_branch": "wip/jgg-for-next",
                    "git_commit_hash": "5e29d1443c46b6ca70a4c940a67e8c09f05dcb7e",
                    "patchset_hash": "",
                    "git_repository_url": "git://git.kernel.org/pub/scm/linux/kernel/git/rdma/rdma.git",
                    "misc": {
                        "pipeline_id": 467715
                    },
                    "id": "origin:1",
                    "origin": "origin",
                    "patchset_files": [],
                    "valid": True,
                },
            ],
        })
        oo_data = oo_client.query(orm.Pattern.parse(">*#"))

        notification_message = NotificationMessage(
            to=["foo@kernelci.org", "bar@kernelci.org"],
            subject='Revision detected: '
            '{% include "revision_summary.txt.j2" %}',
            body='We detected a new revision!\n\n'
            '{% include "revision_description.txt.j2" %}',
            id="id"
        )
        notification = Notification(oo_data["revision"][0],
                                    "subscription",
                                    notification_message)
        self.assertEqual(notification.id,
                         "subscription:revision:"
                         "KCc1ZTI5ZDE0NDNjNDZiNmNhNzBhNGM5NDBhNjdl"
                         "OGMwOWYwNWRjYjdlJywgJycp:aWQ=")
        message = notification.render()
        self.assertIsInstance(message, email.message.EmailMessage)
        self.assertIsNone(message['From'])
        self.assertEqual(message['To'], "foo@kernelci.org, bar@kernelci.org")
        self.assertEqual(message['X-KCIDB-Notification-ID'], notification.id)
        self.assertEqual(message['X-KCIDB-Notification-Message-ID'], "id")
        self.assertIn("Revision detected: ", message['Subject'])
        text, html = message.get_payload()
        self.assertEqual('text/plain', text.get_content_type())
        self.assertEqual('utf-8', text.get_content_charset())
        content = text.get_payload()
        self.assertIn("We detected a new revision!", content)

        self.assertEqual('text/html', html.get_content_type())
        self.assertEqual('utf-8', html.get_content_charset())
        content = html.get_payload()
        self.assertIn("We detected a new revision!", content)
