import helpers.get_date as get_date
import helpers.get_version_info as get_version_info
import helpers.run_errors as run_errors
import helpers.sec_content as sec_content
import post.pallas_beta_releases as pallas_beta_releases
import post.pallas_stable_releases as pallas_stable_releases
import post.sec_content_entry_changes as sec_content_entry_changes
import post.sec_content_ios_modules as sec_content_ios_modules
import post.sec_content_new as sec_content_new
import post.sec_content_zero_days as sec_content_zero_days
from helpers.posted_file import PostedFile
from post.send_post import post


def main():
    # Collect run errors per section, so if one fails, others still try to run
    # but overall the run and the pipeline should fail at the end to indicate issues
    def collect_failed_run(exception: Exception) -> None:
        run_errors.errors.append(exception)
        print("ERROR: " + repr(exception) + "\n")
        # File to disk is only saved on successful post but logic modifies the in memory one as well
        PostedFile.read()

    PostedFile.read()

    # Get stable releases from Pallas
    try:
        stable_releases = pallas_stable_releases.get_stable_releases()
    except Exception as e:
        stable_releases = None
        collect_failed_run(e)

    if stable_releases is not None:
        # Post stable releases from Pallas
        try:
            new_stable_releases = pallas_stable_releases.get_new(pallas_stable_releases.get_latest_versions(stable_releases))
            if new_stable_releases:
                post(pallas_stable_releases.format_releases(new_stable_releases))
        except Exception as e:
            collect_failed_run(e)

        # Post beta releases from Pallas, needs stable releases to tell RCs and old releases apart from new ones
        try:
            new_beta_releases = pallas_beta_releases.get_new(pallas_beta_releases.get_beta_updates(), stable_releases)
            if new_beta_releases:
                post(pallas_beta_releases.format_releases(new_beta_releases))
        except Exception as e:
            collect_failed_run(e)

    # Get all security content rows
    try:
        all_release_rows = sec_content.retrieve_page()
    except Exception as e:
        all_release_rows = None
        collect_failed_run(e)

    if all_release_rows is not None:
        # Post new security content
        try:
            new_sec_content = sec_content_new.get_new(all_release_rows)
            if new_sec_content:
                post(
                    sec_content_new.format_mastodon(new_sec_content),
                    sec_content_new.format_twitter(new_sec_content),
                )
        except Exception as e:
            new_sec_content = None
            collect_failed_run(e)

        # Post iOS modules and zero-days only for new security content if it was posted
        if new_sec_content is not None:
            try:
                ios_release = sec_content_ios_modules.get_new(new_sec_content, get_version_info.latest(all_release_rows))
                if ios_release:
                    post(sec_content_ios_modules.format_release(ios_release))
            except Exception as e:
                collect_failed_run(e)

            try:
                zero_day_releases = sec_content_zero_days.get_new(new_sec_content)
                if zero_day_releases:
                    post(sec_content_zero_days.format_releases(zero_day_releases))
            except Exception as e:
                collect_failed_run(e)

    # Post security content changes
    if get_date.is_midnight() and all_release_rows is not None:
        try:
            # the latest url contains items only 2024+, add at least ones from 2022 and 2023
            all_release_rows_old = sec_content.retrieve_page(sec_content.request_sec_page(sec_content.URL_OLD))

            changed_releases = sec_content_entry_changes.get_changed(all_release_rows + all_release_rows_old)
            if changed_releases:
                post(
                    sec_content_entry_changes.format_mastodon(changed_releases),
                    sec_content_entry_changes.format_twitter(changed_releases),
                )
        except Exception as e:
            collect_failed_run(e)

    # Post yearly report in September
    # DISABLED AS ITS ACCURACY NOT TESTED ENOUGH
    # yearly_reports = sec_content_yearly_report.get_new(new_sec_content, latest_versions)
    # if yearly_reports:
    #     for item in yearly_reports:
    #         post(sec_content_yearly_report.format_report(all_release_rows, item[0], item[1]))

    if run_errors.errors:
        raise ExceptionGroup(f"{len(run_errors.errors)} error(s) during the run", run_errors.errors)


if __name__ == "__main__":
    main()
