#!/usr/bin/env python
# encoding: utf-8


import requests
import json
import time

from xmind2testlink.datatype import TestCase


class XrayIssue:
    def __init__(self, x_acpt, jira_token, xray_client_id=None, xray_client_key=None):
        self.xray_headers = {
            'X-acpt': x_acpt,
            'Content-Type': 'application/json;charset=UTF-8',
        }
        self.jira_headers = {
            'Authorization': 'Basic ' + jira_token,
            'Content-Type': 'application/json',
        }
        self.folder_id = {}
        self.project_id = {
            'KC': '10012',
            'KE': '10005',
            'KM': '10028',
            'KI': '10024',
            'MDX': '10023',
        }

        self.is_smoketest = {
            True: 'Yes',
            False: 'No',
        }

        self.is_need_quard = {
            True: 'Yes',
            False: 'No',
        }

        self.testcase_type = {
            '主流程用例': '主流程用例',
            '分支用例': '分支用例',
            'UED用例': 'UED用例',
            '波及功能用例': '波及功能用例',
        }
        self.srcum_team_jira_type = 'customfield_10089'
        self.xray_client_id = xray_client_id
        self.xray_client_key = xray_client_key
        if self.xray_client_id is not None and self.xray_client_key is not None:
            self.xray_token = self.xray_auth()
            self.bulk_xray_headers = {
                'Authorization': 'Bearer ' + self.xray_token,
                'Content-Type': 'application/json;charset=UTF-8',
            }

    def xray_auth(self):
        auth_url = 'https://xray.cloud.xpand-it.com/api/v1/authenticate'
        auth_payload = {
            'client_id': self.xray_client_id,
            'client_secret': self.xray_client_key,
        }
        res = requests.post(auth_url, json=auth_payload)
        return json.loads(res.content)

    def generate_bulk_json(self, project_name_key, issue_name, test_case, link_issue_key,
                           components, is_smoketest, is_need_quard, testcase_type, forder):
        importance_list = [0, 1, 2, 3]
        importance = 3 if int(test_case.importance) not in importance_list else int(test_case.importance)
        issue_name = str(issue_name).replace('\r\n', '').replace('\r', '').replace('\n', '')
        link_issue_scrum_team_id = self.get_issue_scrum_team_id(link_issue_key)
        steps = []
        for step in test_case.steps:
            step_json = dict()
            step_json['action'] = step.action
            step_json['data'] = ''
            step_json['result'] = step.expected
            steps.append(step_json)
        bulk_json = {
            'testtype': 'Manual',
            'fields': {
                'summary': issue_name,
                'project': {'key': project_name_key},
                'priority': {'name': 'P' + str(importance)},
                'description': 'example of manual test',
                'issuetype': {'name': 'Test'},
                'components': [],
                'assignee': [],
                'customfield_10137': {'value': self.is_smoketest[is_smoketest]},
                'customfield_10139': {'value': self.testcase_type[testcase_type]},
                self.srcum_team_jira_type: {'id': link_issue_scrum_team_id},
                'customfield_10145': {'value': self.is_need_quard[is_need_quard]},
            },
            'update': {
                'issuelinks': [
                    {
                        'add': {
                            'type': {
                                'name': 'Test'
                            },
                            'outwardIssue': {
                                'key': link_issue_key,
                            }
                        }
                    }
                ]
            },
            'steps': steps,
            'xray_test_repository_folder': forder,
        }
        if project_name_key == "KC":
            bulk_json['fields']['components'].append({'name': components})
            bulk_json['fields']['assignee'].append({'id': '5ac2e1fc09ee392b905c0972'})
        return bulk_json

    def bulk_xray_issue(self, bulk_json_arr):
        bulk_url = 'https://xray.cloud.xpand-it.com/api/v1/import/test/bulk'

        try:
            self.xray_token = self.xray_auth()
            res = requests.post(bulk_url, json=bulk_json_arr, headers=self.bulk_xray_headers)
            return json.loads(res.content).get('jobId')
        except Exception as e:
            print('Bulk import xray issue failed {}'.format(e))

    def check_bulk_issue_status(self, job_id):
        """

        :param job_id: bulk issue status
        :return:
        {
            "status": "successful",
            "result": {
                "errors": [],
                "issues": [
                    {
                        "elementNumber": 0,
                        "id": "62372",
                        "key": "KC-6410",
                        "self": "https://olapio.atlassian.net/rest/api/2/issue/62372"
                    }
                ],
                "warnings": []
            }
        }
        """
        check_bulk_url = 'https://xray.cloud.xpand-it.com/api/v1/import/test/bulk/{}/status'.format(job_id)
        try:
            res = requests.get(check_bulk_url, headers=self.bulk_xray_headers)
        except Exception:
            self.xray_token = self.xray_auth()
            res = requests.get(check_bulk_url, headers=self.bulk_xray_headers)
        return json.loads(res.content)

    def await_import_bulk_xray_issue(self, job_id):
        finished_status = ['successful', 'failed', 'unsuccessful']
        res = self.check_bulk_issue_status(job_id)
        while res.get('status') not in finished_status:
            print('Import status is {}, not finished, wait 20 second'.format(res.get('status')))
            time.sleep(20)
            res = self.check_bulk_issue_status(job_id)
        print('Import finished, status is {}'.format(res.get('status')))
        return res

    def create_xray_issue(self, project_name_key, issue_name, importance, link_issue_key,
                          components=None, is_smoketest=False, is_need_quard=False, testcase_type='主流程用例'):
        url = "https://olapio.atlassian.net/rest/api/2/issue"
        importance_list = [0, 1, 2, 3]
        if int(importance) not in importance_list:
            importance = 3
        issue_name = str(issue_name).replace('\r\n', '').replace('\r', '').replace('\n', '')
        link_issue_scrum_team_id = self.get_issue_scrum_team_id(link_issue_key)
        payload = {
            "fields": {
                "project": {"key": project_name_key},
                "summary": issue_name,
                "priority": {"name": "P" + str(importance)},
                "description": "example of manual test",
                "issuetype": {"name": "Test"},
                'components': [],
                'assignee': [],
                'customfield_10137': {'value': self.is_smoketest[is_smoketest]},
                'customfield_10139': {'value': self.testcase_type[testcase_type]},
                self.srcum_team_jira_type: {'id': link_issue_scrum_team_id},
                'customfield_10145': {'value': self.is_need_quard[is_need_quard]},
            }
        }
        if project_name_key == "KC":
            payload['fields']['components'].append({'name': components})
            payload['fields']['assignee'].append({'id': '5ac2e1fc09ee392b905c0972'})

        response = requests.request("POST", url, headers=self.jira_headers, data=json.dumps(payload))
        if response.status_code >= 400:
            print('创建issue 状态码为{}'.format(response.status_code))
            print('create jira issue failed, {}'.format(response.content.decode(encoding='utf-8')))
            print(response.json()['key'])
        print('成功创建了xray issue https://olapio.atlassian.net/browse/' + response.json()['key'])
        return response.json()['id'], response.json()['key']

    # 2. 给issue新增step, 替换url中的id

    def create_xray_issue_step(self, key, index, action, data, result):
        create_step_url = 'https://xray.cloud.xpand-it.com/api/internal/test/' + key + '/step'
        data = {"id": "-1", "index": index, "customFields": [], "action": action, "data": data, "result": result}

        response = requests.post(create_step_url, headers=self.xray_headers, data=json.dumps(data))
        if response.status_code == 500:
            print(response.json()['error'])
            exit(1)
        # else:
        #     print('创建步骤成功')

    def create_xray_full_issue(self, project_name_key, issue_name, test_case, link_issue_key,
                               components, is_smoketest, is_need_quard, testcase_type):
        # test_case = TestCase(test_case)
        (issue_id, issue_key) = self.create_xray_issue(project_name_key, issue_name, test_case.importance,
                                                       link_issue_key, components, is_smoketest,
                                                       is_need_quard, testcase_type)
        self.link_issue(link_issue_key, issue_key)
        # self.get_folder_id(project_name_key)
        for i in range(len(test_case.steps)):
            step = test_case.steps[i]
            self.create_xray_issue_step(issue_id, i, step.action, '', step.expected)
        # self.move_issue_to_folder(issue_id, project_name_key, components)
        return issue_id

    def move_issue_to_folder(self, issue_ids, project_name_key, components):
        move_url = 'https://xray.cloud.xpand-it.com/api/internal/test-repository/move-tests-to-folder'
        data = {
            'folderId': self.folder_id[components],
            'issueIds': issue_ids,
            'skipTestValidation': False,
            'projectId': self.project_id[project_name_key],
        }
        response = requests.post(move_url, headers=self.xray_headers, data=json.dumps(data))
        print(response.status_code)
        if response.status_code >= 400:
            print(response.content)

    def get_folder_id(self, project_name_key):
        get_folder_url = 'https://xray.cloud.xpand-it.com/api/internal/test-repository'
        data = {
            'projectId': self.project_id[project_name_key],
        }
        response = requests.post(get_folder_url, headers=self.xray_headers, data=json.dumps(data))
        print(response.status_code)
        if response.status_code >= 400:
            print(response.content)
        for folder in json.loads(response.content).get('folders'):
            self.folder_id[folder.get('name')] = folder.get('folderId')

    def link_issue(self, origin_key, xray_key):
        url = 'https://olapio.atlassian.net/rest/api/2/issueLink'

        # payload = {"type": {"id": "10006"}, "inwardIssue": {"key": "KE-12706"}, "outwardIssue": {"key": "QUARD-263"}}
        payload = {"type": {"id": "10006"}, "inwardIssue": {"key": origin_key}, "outwardIssue": {"key": xray_key}}

        response = requests.request("POST", url, headers=self.jira_headers, data=json.dumps(payload))
        # return response.json()['id']

    def get_issue_scrum_team_id(self, issue_key):
        res = self.get_issue_info(issue_key)
        if self.srcum_team_jira_type not in res.get('fields').keys():
            print('{} has not scrum team property, please add it')
            raise None
        return res.get('fields').get(self.srcum_team_jira_type).get('id')

    def get_issue_info(self, issue_key):
        url = "https://olapio.atlassian.net/rest/api/2/issue/{}".format(issue_key)

        payload = {}

        response = requests.request("GET", url, headers=self.jira_headers, data=payload)

        return json.loads(response.content)


# create_xray_full_issue()
if __name__ == '__main__':
    X_acpt = ''
    xray_headers = {
        'X-acpt': X_acpt,
        'Content-Type': 'application/json;charset=UTF-8',
    }
    jira_token = ''
    xray_issue = XrayIssue(X_acpt, jira_token,
                           '',
                           '')
    res = xray_issue.xray_auth()
    print(res)
    # project_name_key = 'QUARD'
    # issue_name = 'test_issue'
    # test_case = ''
    # link_issue_key = ''
    # xray_issue.create_xray_full_issue(project_name_key, issue_name, test_case, link_issue_key)
