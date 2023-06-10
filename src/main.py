import helpers.get_date as get_date
import helpers.get_version_info as get_version_info
import helpers.post_format as post_format
import post.rss_releases as rss_releases
import post.sec_content as sec_content
from helpers.PostedFile import PostedFile
from post.send_post import post


def main():
    all_release_rows = sec_content.retrieve_page()
    latest_versions = get_version_info.latest(all_release_rows[:20])

    PostedFile.read()

    new_sec_content = sec_content.get_new(all_release_rows)
    new_sec_content += sec_content.get_if_available(all_release_rows)
    ios_release = sec_content.get_new_ios_release(new_sec_content, latest_versions)
    zero_day_releases = sec_content.get_new_zero_days(new_sec_content)
    # yearly_reports = releases_sec.get_yearly_report(new_sec_content, latest_versions)  # DISABLED AS NOT TESTED ENOUGH

    new_releases_rss = rss_releases.get_new()

    if ios_release:
        post(post_format.top_ios_modules(ios_release))

    if zero_day_releases:
        post(post_format.zero_days(zero_day_releases))

    if get_date.is_midnight():
        changed_releases = sec_content.get_entry_changes(all_release_rows)
        post(post_format.entry_changes(changed_releases))

    # if yearly_reports:
    #     for item in yearly_reports:
    #         post(post_format.yearly_report(all_release_rows, item[0], item[1]))

    # new updates should be posted last, after all of the other posts
    if new_releases_rss:
        post(post_format.new_updates(new_releases_rss))

    if new_sec_content:
        post(post_format.new_security_content(new_sec_content))

    PostedFile.save()


if __name__ == "__main__":
    main()
