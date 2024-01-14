class Rule:
    def evaluate(self, data: dict) -> bool:
        raise NotImplementedError("Subclasses must implement evaluate method.")


class TargetCustomerDefinedRule(Rule):
    def evaluate(self, data: dict) -> bool:
        return 'target_customer' in data and data['target_customer'] is not None


class LeadListNotEmptyRule(Rule):
    def evaluate(self, data: dict) -> bool:
        return len(data.get('lead_list', [])) > 0


class EmailContentValidRule(Rule):
    def evaluate(self, data: dict) -> bool:
        # Here, you'd define what makes the email content 'valid'
        return 'email_content' in data and data['email_content'] is not None
