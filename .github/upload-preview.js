import { Octokit } from '@octokit/rest';
const { default: surge } = await import('surge');
const octokit = new Octokit({ auth: process.env.GH_PR_TOKEN });
const publishFn = surge().publish();

// From github actions
const ghrepo = process.env.GITHUB_REPOSITORY || '';
const [owner, repo] = ghrepo.split('/');
const prnum = process.env.GH_PR_NUM;
const prbranch = process.env.GITHUB_REF.split('/').pop();

const uploadFolder = process.argv[2];
if (!uploadFolder) {
  process.exit(1);
}

let uploadURL = `${repo}-${prnum ? `pr-${prnum}` : prbranch}`.replace(/[/|.]/g, '-');
uploadURL += ".surge.sh"


publishFn({
  project: uploadFolder,
  p: uploadFolder,
  domain: uploadURL,
  d: uploadURL,
  e: 'https://surge.surge.sh',
  endpoint: 'https://surge.surge.sh'
});

function tryAddComment(comment, commentBody) {
  if (!commentBody.includes(comment)) {
    return comment;
  }
  return '';
}

if (prnum) {
  octokit.issues
    .listComments({
      owner,
      repo,
      issue_number: prnum
    })
    .then((res) => res.data)
    .then((comments) => {
      let commentBody = '';
      const existingComment = comments.find((comment) => comment.user.login === 'openssl-machine');
      if (existingComment) {
        commentBody += existingComment.body.trim();
        commentBody += '\n\n';
      }

      commentBody += tryAddComment(`Preview: https://${uploadURL}`, commentBody);

      if (existingComment) {
        octokit.issues
          .updateComment({
            owner,
            repo,
            comment_id: existingComment.id,
            body: commentBody
          })
          .then(() => console.log('Updated comment!'));
      } else {
        octokit.issues
          .createComment({
            owner,
            repo,
            issue_number: prnum,
            body: commentBody
          })
          .then(() => console.log('Created comment!'));
      }
    });
}
