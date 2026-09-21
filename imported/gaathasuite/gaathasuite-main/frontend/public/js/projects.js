async function deleteProject(id){ if(!confirm('Delete project?')) return; await apiDelete(`/projects/project/${id}/delete`); }
