// LeetCode GraphQL helpers. Paste ONE function body (or the whole file plus a call) into
// mcp__Claude_Browser__javascript_tool on the logged-in LeetCode tab. All calls are read-only.
// Tool calls time out at 45 s, so keep loops short (batch ~10 slugs per call).

const gql = async (query, variables) => {
  const r = await fetch('/graphql/', { method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ query, variables }) });
  return r.json();
};

// 1. Is the pane logged in? Returns username or null.
async function whoami() {
  const j = await gql(`query { userStatus { username isSignedIn isPremium } }`, {});
  return j.data && j.data.userStatus;
}

// 2. All accepted problems (paginated, ~100 per page). Returns "id|title" lines.
async function acceptedList() {
  const q = `query p($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
    problemsetQuestionList: questionList(categorySlug: $categorySlug, limit: $limit, skip: $skip, filters: $filters) {
      total: totalNum questions: data { title titleSlug frontendQuestionId: questionFrontendId } } }`;
  const out = []; let skip = 0, total = null, pages = 0;
  while ((total === null || skip < total) && pages < 10) {
    const j = await gql(q, { categorySlug: 'all-code-essentials', limit: 100, skip, filters: { status: 'AC' } });
    const d = j.data.problemsetQuestionList; total = d.total;
    d.questions.forEach(x => out.push(x.frontendQuestionId + '|' + x.titleSlug + '|' + x.title));
    skip += 100; pages++;
  }
  return 'TOTAL ' + total + '\n' + out.join('\n');
}

// 3. Latest accepted submission for a list of slugs.
// NOTE: this is SUBMISSION history only. LeetCode exposes no run-code history - there is no
// recentRunList / interpret query, and Run results are returned inline by the REST judge at run
// time and never stored per problem. So "failed" here always means failed *submissions*; time
// spent failing against the sample cases with the Run button is invisible to this system.
//
// Pass sinceTs (unix seconds, e.g. the logged `start` time) to scope the failure count to THIS
// attempt. Without it, failedAllTime counts every non-accepted submission going back years, which
// silently pushes a clean attempt to `sloppy`.
// Returns [{slug, id, ts, lang, runtime, memory, failedSince, failedAllTime, acceptedSince, firstTs, total}].
async function latestAccepted(slugs, sinceTs) {
  const q = `query s($questionSlug: String!, $offset: Int!, $limit: Int!) {
    questionSubmissionList(questionSlug: $questionSlug, offset: $offset, limit: $limit) {
      submissions { id statusDisplay lang timestamp runtime memory } } }`;
  const out = [];
  const since = sinceTs ? +sinceTs : null;
  for (const slug of slugs) {
    const j = await gql(q, { questionSlug: slug, offset: 0, limit: 20 });
    const subs = (j.data && j.data.questionSubmissionList && j.data.questionSubmissionList.submissions) || [];
    const ac = subs.find(s => s.statusDisplay === 'Accepted');
    const firstTs = subs.length ? Math.min(...subs.map(s => +s.timestamp)) : null;
    const failedBetween = (lo) => ac ? subs.filter(s =>
      s.statusDisplay !== 'Accepted' && +s.timestamp < +ac.timestamp && (lo === null || +s.timestamp >= lo)).length : 0;
    out.push({ slug, id: ac ? ac.id : null, ts: ac ? +ac.timestamp : null, lang: ac ? ac.lang : null,
      runtime: ac ? ac.runtime : null, memory: ac ? ac.memory : null,
      failedSince: since === null ? null : failedBetween(since),
      failedAllTime: failedBetween(null),
      acceptedSince: ac && since !== null ? (+ac.timestamp >= since) : null,
      firstTs, total: subs.length });
  }
  return JSON.stringify(out);
}

// 4. Code of one submission by id. Returns JSON {code, lang, timestamp, runtime, memory}.
async function submissionCode(id) {
  const q = `query d($submissionId: Int!) { submissionDetails(submissionId: $submissionId) {
    code timestamp runtime memory lang { name } statusCode } }`;
  const j = await gql(q, { submissionId: +id });
  const d = j.data && j.data.submissionDetails;
  return JSON.stringify(d ? { code: d.code, lang: d.lang && d.lang.name, timestamp: d.timestamp, runtime: d.runtime, memory: d.memory } : null);
}

// 5. Codes for several slugs in one call (latest accepted each). Pass sinceTs to scope the failure
// count to this attempt (see note on latestAccepted). Returns JSON
// {slug: {code, ts, lang, failedSince, failedAllTime, firstTs}}.
async function codesFor(slugs, sinceTs) {
  const meta = JSON.parse(await latestAccepted(slugs, sinceTs));
  const out = {};
  for (const m of meta) {
    if (!m.id) { out[m.slug] = null; continue; }
    const c = JSON.parse(await submissionCode(m.id));
    out[m.slug] = c ? { code: c.code, ts: m.ts, lang: c.lang, failedSince: m.failedSince,
                        failedAllTime: m.failedAllTime, firstTs: m.firstTs } : null;
  }
  return JSON.stringify(out);
}

// Example call (append after the definitions when pasting):
// await codesFor(['two-sum','lru-cache'])
