Within context are the Pydantic models that are used for context attached to either nodes or data objects.
Knowledge are context items like target customer or sales strategy.
Settings are things like number of leads or email cadence that affect the behaviour

## Settings

Each node within its context can have settings that dictate behaviour when the node executes, or what the user can do as input to that node. For example a send email output node may have a setting for how many emails it sends from the queue each hour, or a generate lead list process node may have a setting for how many leads to gather as default. We can map the settings to the nodes rather than workflow_node as each node type will have the same potential settings. Settings will potentially need to be validated using the node instance as well as the data object instance, for example the number of emails a generate email process node can generate must be a multiple of the number of leads that have been previously gathered. I was thinking we would write a base class that took a value and then optionally some node(s) and a data object and then validated conditionally whether this value was acceptable. We would then have sub-classes that implemented the conditional logic for each setting. We would then store the class name of the setting class in the DB and use that class name in the node context dictionary similar to how we do for knowledge context items.

