import os
import json
import subprocess
import time
import pytest
import allure
from utils.ai_data_generator import get_test_data


@allure.epic("Mobile eWork")
@allure.feature("Customer Management")
class TestCustomerCreation:
    # Take data from ai data generator dan put it to the maestro test scenario
    @allure.title("Create Customer - AI Data")
    def test_create_customer(self, tmp_path):
        test_data = get_test_data()
        allure.attach(
            json.dumps(test_data, indent=2),
            name="Test Data (AI/Faker)",
            attachment_type=allure.attachment_type.JSON,
        )

        env_vars = {
            "OUTLET_NAME": test_data["customer_name"],
            "PHONE": test_data["customer_contact"],
            "ADDRESS": test_data["customer_address"],
            "EMAIL": test_data["customer_email"],
            "CONTACT_PERSON": test_data["contact_person"],
        }
        env_args = " ".join([f'-e {k}="{v}"' for k, v in env_vars.items()])

        # record file for allure attachment
        record_file = tmp_path / "record.mp4"
        device_video_path = "/sdcard/maestro_record.mp4"

        # Command Maestro normal
        cmd = f"maestro test maestro/ {env_args} --format junit"

        with allure.step("Run Maestro Automation"):
            # 1. Mulai rekam layar di background melalui ADB
            subprocess.Popen(f"adb shell screenrecord {device_video_path}", shell=True)

            # 2. Eksekusi Maestro
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=True,
                stdin=subprocess.DEVNULL,
            )

            # 3. Hentikan perekaman dengan aman (kirim sinyal interrupt ke screenrecord)
            subprocess.run("adb shell pkill -2 screenrecord", shell=True)
            time.sleep(
                2
            )  # Beri jeda 2 detik agar Android selesai memproses/menyimpan file video

            # 4. Tarik (pull) file video dari emulator ke laptop (ke tmp_path)
            subprocess.run(
                f"adb pull {device_video_path} {str(record_file)}",
                shell=True,
                capture_output=True,
            )

            # --- Lampirkan Log Teks ---
            allure.attach(
                result.stdout,
                name="Maestro Stdout",
                attachment_type=allure.attachment_type.TEXT,
            )
            if result.stderr:
                allure.attach(
                    result.stderr,
                    name="Maestro Stderr",
                    attachment_type=allure.attachment_type.TEXT,
                )

            # --- Lampirkan Video JIKA GAGAL ---
            # Jika returncode bukan 0 (karena ada tes yang fail), video akan dilampirkan
            if result.returncode != 0:
                if record_file.exists():
                    allure.attach.file(
                        str(record_file),
                        name="Execution Recording (Failed)",
                        attachment_type=allure.attachment_type.MP4,
                    )

            # 5. Hapus video di dalam emulator agar memori tidak penuh
            subprocess.run(f"adb shell rm {device_video_path}", shell=True)

            # 6. Validasi akhir Pytest
            assert result.returncode == 0, "Maestro test execution failed"
