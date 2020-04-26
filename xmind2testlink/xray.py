#!/usr/bin/env python
# encoding: utf-8


import requests, json

from xmind2testlink.datatype import TestCase


class xray_issue:

    def create_xray_issue(project_name_key, issue_name, jira_token):
        url = "https://olapio.atlassian.net/rest/api/2/issue"

        payload = {
            "fields": {"project": {"key": project_name_key}, "summary": issue_name,
                       "description": "example of manual test",
                       "issuetype": {"name": "Test"}}}
        headers = {
            'Authorization': 'Basic ' + jira_token,
            'Content-Type': 'application/json',
        }

        response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
        print('成功创建了xray issue https://olapio.atlassian.net/browse/' + response.json()['key'])
        return response.json()['id'], response.json()['key']

    # 2. 给issue新增step, 替换url中的id

    def create_xray_issue_step(key, index, action, data, result, X_acpt):
        headers = {
            'X-acpt': X_acpt,
            'Content-Type': 'application/json;charset=UTF-8',
        }

        data = {"id": "-1", "index": index, "customFields": [], "action": action, "data": data, "result": result}

        response = requests.post('https://xray.cloud.xpand-it.com/api/internal/test/' + key + '/step', headers=headers,
                                 data=json.dumps(data))

    def create_xray_full_issue(project_name_key, issue_name, test_case, link_issue_key, jira_token, X_acpt):
        # test_case = TestCase(test_case)
        (id, key) = xray_issue.create_xray_issue(project_name_key, issue_name, jira_token)
        xray_issue.link_issue(link_issue_key, key, jira_token)

        for i in range(len(test_case.steps)):
            step = test_case.steps[i]
            xray_issue.create_xray_issue_step(id, i, step.action, '', step.expected, X_acpt)

    def link_issue(origin_key, xray_key, jira_token):
        url = 'https://olapio.atlassian.net/rest/api/2/issueLink'

        # payload = {"type": {"id": "10006"}, "inwardIssue": {"key": "KE-12706"}, "outwardIssue": {"key": "QUARD-263"}}
        payload = {"type": {"id": "10006"}, "inwardIssue": {"key": origin_key}, "outwardIssue": {"key": xray_key}}
        headers = {
            'Authorization': 'Basic ' + jira_token,
            'Content-Type': 'application/json',
        }

        response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
        # return response.json()['id']

    def get_issue_info(self):
        import requests

        url = "https://olapio.atlassian.net/rest/api/2/issue/QUARD-263"

        payload = {}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic ' + jira_token,
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.text.encode('utf8'))


# create_xray_full_issue()
if __name__ == '__main__':
    X_acpt = ''
    jira_token = 'XWGNZ4MgoeD1kfofTelQ72CD'
    xray_issue = xray_issue()
    # xray_issue.get_issue_info()
    project_name_key = 'QUARD'
    issue_name = 'test_issue'
    test_case = ''
    link_issue_key = ''
    xray_issue.create_xray_full_issue(project_name_key, issue_name, test_case, link_issue_key)
