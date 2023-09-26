import helpers.get_date as get_date
import helpers.get_version_info as get_version_info
import post.rss_releases as rss_releases
import post.sec_content as sec_content
from helpers.posted_file import PostedFile
from post.send_post import post


def main():
    all_release_rows = sec_content.retrieve_page()
    latest_versions = get_version_info.latest(all_release_rows[:20])

    PostedFile.read()

    new_releases_rss = rss_releases.get_new()
    if new_releases_rss:
        post(rss_releases.format_releases(new_releases_rss))

    new_sec_content = sec_content.get_new(all_release_rows)
    if new_sec_content:
        post(
            sec_content.format_new_sec_content_mastodon(new_sec_content),
            sec_content.format_new_sec_content_twitter(new_sec_content),
        )

    ios_release = sec_content.get_new_ios_release(new_sec_content, latest_versions)
    if ios_release:
        post(sec_content.format_ios_release(ios_release))

    zero_day_releases = sec_content.get_new_zero_days(new_sec_content)
    if zero_day_releases:
        post(sec_content.format_zero_days(zero_day_releases))

    if get_date.is_midnight():
        changed_releases = sec_content.get_entry_changes(all_release_rows)
        if changed_releases:
            post(
                sec_content.format_entry_changes_mastodon(changed_releases),
                sec_content.format_entry_changes_twitter(changed_releases),
            )

    # DISABLED AS ITS ACCURACY NOT TESTED ENOUGH
    # yearly_reports = releases_sec.get_yearly_report(new_sec_content, latest_versions)
    # if yearly_reports:
    #     for item in yearly_reports:
    #         post(sec_content.format_yearly_report(all_release_rows, item[0], item[1]))


if __name__ == "__main__":
    main()
