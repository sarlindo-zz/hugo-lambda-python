import json
import subprocess
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

tmp_dir = '/tmp/sources'
dest_dir = '/tmp/sources/public'

def generate_site(source_bucket, dest_bucket):

    logger.info(' '.join(["./dist/aws", "s3", "cp",
         "--exclude", ".git/*",
         "--recursive",
         "s3://" + source_bucket, tmp_dir,
         ]))
    sync = subprocess.Popen(
        ["./dist/aws", "s3", "cp",
         "--exclude", ".git/*",
         "--recursive",
         "s3://" + source_bucket, tmp_dir,
         ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = sync.communicate()

    if sync.returncode != 0:
        logger.error("Failure syncing down site, exit code %d" % sync.returncode)
        logger.error("---stdout---\r\n%s\r\n---end stdout---" % stdout)
        logger.error("---stderr---\r\n%s\r\n---end stderr---" % stderr)
        return

    logger.info(' '.join(["./dist/hugo", "-v", "--source",
         tmp_dir, "--destination", dest_dir,
         ]))
    # download files to TMP
    hugo = subprocess.Popen(
        ["./dist/hugo", '-v', '--source', tmp_dir, '--destination', dest_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = hugo.communicate()

    if hugo.returncode != 0:
        logger.error("Hugo exited with code %d" % hugo.returncode)
        logger.error("---stdout---\r\n%s\r\n---end stdout---" % stdout)
        logger.error("---stderr---\r\n%s\r\n---end stderr---" % stderr)
    else:
        logger.info("Hugo exited with code %d" % hugo.returncode)
        logger.info("---stdout---\r\n%s\r\n---end stdout---" % stdout)
        logger.info("---stderr---\r\n%s\r\n---end stderr---" % stderr)

    logger.info(' '.join(["./dist/aws", "s3", "sync",
         "--acl", "public-read", dest_dir,"s3://" + dest_bucket,
         ]))

    sync = subprocess.Popen(
        ["./dist/aws", "s3", "sync",
         "--acl", "public-read",
         dest_dir, "s3://" + dest_bucket,
         ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = sync.communicate()

    if sync.returncode != 0:
        logger.error("Failure saving site results, exit code %d" % sync.returncode)
        logger.error("---stdout---\r\n%s\r\n---end stdout---" % stdout)
        logger.error("---stderr---\r\n%s\r\n---end stderr---" % stderr)
        return


def handler(event, context):
    logger.info(json.dumps(event))
    key = event['Records'][0]['s3']['object']['key']
    source_bucket = event['Records'][0]['s3']['bucket']['name']

    dest_bucket = source_bucket.replace('input.', '')

    logger.info("source bucket " + source_bucket)
    logger.info("dest bucket " + dest_bucket)
    logger.info("key " + key)

    if key.startswith('.git/'):
        logger.info("Git file, skipping.")
        return
    if key.endswith('/'):
        logger.info("Directory, skipping.")
        return
    else:
	# always generate the whole site, even static content forces a regenerate
        generate_site(source_bucket, dest_bucket)
