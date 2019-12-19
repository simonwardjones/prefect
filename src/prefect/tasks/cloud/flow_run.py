from typing import Any
from prefect import Task

from prefect.client import Client
from prefect.utilities.tasks import defaults_from_attrs
from prefect.utilities.graphql import with_args


class FlowRunTask(Task):
    """
    Task used to kick off a Flow Run in Cloud.
    """

    def __init__(
        self,
        flow_name: str = None,
        project_name: str = None,
        parameters: dict = None,
        **kwargs: Any
    ):
        self.flow_name = flow_name
        self.project_name = project_name
        self.parameters = parameters
        self.client = Client()
        super().__init__(**kwargs)

    @defaults_from_attrs("project_name", "flow_name", "parameters")
    def run(
        self, project_name: str = None, flow_name: str = None, parameters: dict = None
    ) -> None:
        """
        Run method for the task; responsible for scheduling the specified flow run.

        Args:
            - project_name (str, optional): the project in which the flow is located; if not provided, this method
                will use the project provided at initialization
            - flow_name (str, optional): the name of the flow to schedule; if not provided, this method will
                use the project provided at initialization
            - parameters (dict, optional): the parameters to pass to the flow run being scheduled; if not provided,
                this method will use the parameters provided at initialization

        Returns:
            - None
        """
        # verify that flow and project names were passed in some capacity or another
        if project_name is None:
            raise ValueError("Must provide a project name.")
        if flow_name is None:
            raise ValueError("Must provide a flow name.")

        # find the flow ID to schedule
        query = {
            "query": {
                with_args(
                    "flow",
                    {
                        "where": {
                            "name": {"_eq": flow_name},
                            "project": {"name": {"_eq": project_name}},
                        }
                    },
                ): {"id"}
            }
        }
        flow = self.client.graphql(query).data.flow
        # verify that an ID was returned
        if not flow:
            raise ValueError(
                "No flow {} found in project {}.".format(flow_name, project_name)
            )
        # and that there was only one ID returned
        if len(flow) > 1:
            raise ValueError(
                "More than one flow named {} found in project {}.".format(
                    flow_name, project_name
                )
            )
        flow_id = flow[0].id
        self.client.create_flow_run(flow_id=flow_id, parameters=parameters)
