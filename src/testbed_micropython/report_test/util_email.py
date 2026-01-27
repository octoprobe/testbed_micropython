import datetime
import logging
import os
import pathlib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__file__)


class EmailSmtp:
    def __init__(self) -> None:
        def environ_get(name: str) -> str:
            try:
                return os.environ[name]
            except KeyError as e:
                raise ValueError(
                    f"Environment variable expected but not defined: '{name}'"
                ) from e

        self.smtp_port = 587  # 465, 2465, 587, 2587
        self.smtp_host = environ_get("OCTOPROBE_SMTP_HOST")
        self.smtp_username = environ_get("OCTOPROBE_SMTP_USERNAME")
        self.smtp_password = environ_get("OCTOPROBE_SMTP_PASSWORD")

    def send(
        self,
        receipients: list[str],
        filename_summary_report: pathlib.Path,
        subject: str,
        from_address: str,
    ) -> None:
        assert isinstance(receipients, list)
        assert len(receipients) > 0
        assert isinstance(filename_summary_report, pathlib.Path)
        assert filename_summary_report.exists(), filename_summary_report

        # Read the HTML report
        html_body = filename_summary_report.read_text()

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_address
        msg["To"] = ", ".join(receipients)

        # Attach HTML content
        html_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(html_part)

        try:
            logger.info(
                f"Sending email to {len(receipients)} recipient(s): {', '.join(receipients)}"
            )
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(
                    from_addr=from_address,
                    to_addrs=receipients,
                    msg=msg.as_string(),
                )
            logger.info("Email sent successfully")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")


def main() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.debug("Send test email")
    email_smtp = EmailSmtp()
    email_smtp.send(
        receipients=["hans.maerki@gmail.com"],
        subject=f"Test {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        from_address="Hans Maerki<buhtig.hans.maerki@ergoinfo.ch>",
        # filename_summary_report=pathlib.Path(__file__),
        filename_summary_report=pathlib.Path(
            "/home/maerki/work_octoprobe/testbed_micropython/testresults/octoprobe_summary_report.html"
        ),
    )


if __name__ == "__main__":
    main()
