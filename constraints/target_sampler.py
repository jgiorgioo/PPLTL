from .target_extractors import get_random_target

class TargetSampler:
    def __init__(self, domain: str, constraint_name: str, plan_path: str, problem_path: str):
        self.domain = domain
        self.constraint_name = constraint_name
        self.plan_path = plan_path
        self.problem_path = problem_path
        self._blacklisted = set()
        self._next_target = None
        self._exhausted = False

    def has_candidates(self) -> bool:
        if self._exhausted:
            return False
            
        if self._next_target is None:
            # Pass everything uniformly, including the stateful blacklist
            self._next_target = get_random_target(
                domain=self.domain,
                constraint=self.constraint_name,
                plan_path=self.plan_path,
                problem_path=self.problem_path,
                blacklist=self._blacklisted
            )
            if self._next_target is None:
                self._exhausted = True
                return False
        return True

    def sample_next_target(self):
        if not self.has_candidates():
            return None
        target = self._next_target
        self._next_target = None
        return target

    def mark_as_failed(self, target):
        self._blacklisted.add(target)