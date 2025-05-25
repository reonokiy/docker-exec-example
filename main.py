import docker
import docker.errors
import tempfile
from pydantic import BaseModel


class DockerExecResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int


def docker_exec_python_code(
    image: str = "python:3.11",
    code: str = "print('Hello from Docker!')",
    timeout: int = 10,
) -> DockerExecResponse:
    """
    Executes Python code in a Docker container.

    :param image: Docker image to use.
    :param code: Python code to execute.
    :param command: Command to run the code.
    :param timeout: Timeout for the command execution.
    :return: Output of the executed code.
    """
    client = docker.from_env()
    # write code to a temporary file
    tmp_code_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    try:
        tmp_code_file.write(code.encode("utf-8"))
        tmp_code_file.close()
        code = tmp_code_file.name
    except Exception as e:
        raise RuntimeError(f"Failed to write code to temporary file: {e}")

    try:
        # mount the temporary file into the container
        volumes = {tmp_code_file.name: {"bind": "/tmp/code.py", "mode": "rw"}}
        container = client.containers.run(
            image,
            command="python /tmp/code.py",
            detach=True,
            auto_remove=False,
            network_disabled=True,
            volumes=volumes,
        )
        exit_code = container.wait(timeout=timeout)
        stdout = container.logs(stdout=True, stderr=False, stream=False).decode("utf-8")
        stderr = container.logs(stdout=False, stderr=True, stream=False).decode("utf-8")
        container.remove(force=True)  # Clean up the container after execution
        return DockerExecResponse(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code["StatusCode"],
        )
    except docker.errors.ContainerError as e:
        raise RuntimeError(f"Container error: {e}")


def main():
    test_docker_connection()
    code = "print('Hello from Docker!')"
    response = docker_exec_python_code(code=code)
    print(f"Output:\n{response}")


def test_docker_connection():
    try:
        client = docker.from_env()
        client.ping()
        print("Docker connection successful!")
    except docker.errors.DockerException as e:
        print(f"Failed to connect to Docker: {e}")


if __name__ == "__main__":
    main()
