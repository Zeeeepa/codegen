    def get_modified_symbols_in_pr(self, pr_id: int) -> tuple[str, dict[str, str], list[str], str]:
        """Get all modified symbols in a pull request"""
        pr = self._op.get_pull_request(pr_id)
        cg_pr = CodegenPR(self._op, self, pr)
        patch = cg_pr.get_pr_diff()
        commit_sha = cg_pr.get_file_commit_shas()
        return patch, commit_sha, cg_pr.modified_symbols, pr.head.ref

    def create_pr_comment(self, pr_number: int, body: str) -> None:
        """Create a comment on a pull request"""
